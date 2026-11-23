"""Offline acceptance report, with an optional separately labelled real-model run."""
import argparse
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from time import perf_counter
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.request import urlopen

import app

HERE = Path(__file__).parent
APPROVAL = "2026-06-15"
REVIEW = "待覆核"
REJECTED = "拒絕輸入"


def baseline(contract, report):
    """Exact labels, last match wins, required fields plus missing assurance."""
    if not contract.strip() or not report.strip():
        return REJECTED, {}, {}
    labels = {label: name for name, label in app.FIELDS.items()}
    evidence = {}
    for document, content in (("合約", contract), ("盤查及查證摘要", report)):
        for number, line in enumerate(content.splitlines(), 1):
            label, _, value = line.partition("：")
            if label in labels and value.strip():
                evidence[labels[label]] = {(value.strip(), f"{document} 第{number}行", line)}
    if set(evidence) != set(app.FIELDS):
        return REVIEW, {}, evidence
    fields = {key: next(iter(items))[0] for key, items in evidence.items()}
    if fields["assurance"] == "是" and fields["verified"] != "是":
        return REVIEW, {}, evidence
    try:
        reduction = (Decimal(fields["baseline"]) - Decimal(fields["actual"])) / Decimal(fields["baseline"]) * 100
        hit = reduction >= Decimal(fields["target"])
    except (InvalidOperation, ZeroDivisionError):
        return REVIEW, {}, evidence
    approved = date.fromisoformat(APPROVAL)
    effective = date(approved.year + approved.month // 12, approved.month % 12 + 1, 1)
    return ("達標" if hit else "未達標"), {
        "利差調整bps": fields["hit" if hit else "miss"],
        "生效日": effective.isoformat(),
    }, evidence


def assess(contract, report, mode):
    if not contract.strip() or not report.strip():
        return REJECTED, {}, {}
    response = app.run_agent(contract, report, mode)
    evidence = {name: {(item["value"], item["source"], item["quote"]) for item in items}
                for name, items in response["evidence"].items() if items}
    if response["flags"]:
        return REVIEW, {}, evidence
    result = app.calculate(response["fields"], APPROVAL)
    return result["判定"], result, evidence


def evaluate(cases, engine, repeat):
    stats = Counter()
    details = []
    for case in cases:
        contract, report = case["contract"], case["annual_reports"]["2025"]
        start = perf_counter()
        status, result, evidence = engine(contract, report)
        elapsed = (perf_counter() - start) * 1000
        if repeat:
            stats["same"] += engine(contract, report) == (status, result, evidence)
        evidence_matches = not evidence
        if report:
            expected = {key: {tuple(item) for item in items} for key, items in case["expected_evidence"].items()}
            evidence_matches = evidence == expected
            stats["fields_total"] += len(app.FIELDS)
            stats["fields_ok"] += sum(
                {item[0] for item in evidence.get(key, set())} == {item[0] for item in expected.get(key, set())}
                for key in app.FIELDS)
            stats["sources_total"] += sum(map(len, expected.values()))
            stats["sources_ok"] += sum(len(found & evidence.get(key, set())) for key, found in expected.items())
            stats["claims"] += sum(map(len, evidence.values()))
            stats["unsupported"] += sum(len(found - expected.get(key, set())) for key, found in evidence.items())
        expected_status = case["expected"]
        is_exception = expected_status in (REVIEW, REJECTED)
        exact_status = status == expected_status
        stats["status_ok"] += exact_status
        stats["exception_total" if is_exception else "normal_total"] += 1
        if is_exception:
            stats["exception_ok"] += exact_status
            stats["missed"] += status not in (REVIEW, REJECTED)
        else:
            stats["false_positive"] += status in (REVIEW, REJECTED)
            stats["adjustment_ok"] += (exact_status and result.get("利差調整bps") == case["expected_bps"]
                                       and result.get("生效日") == case["expected_effective"])
        matches = (exact_status and evidence_matches
                   and result.get("利差調整bps") == case["expected_bps"]
                   and result.get("生效日") == case["expected_effective"])
        stats["ms"] += elapsed
        details.append({"id": case["id"], "案例": case["title"], "預期": expected_status, "實際": status,
                        "基點": result.get("利差調整bps"), "生效日": result.get("生效日"),
                        "預期基點": case["expected_bps"], "預期生效日": case["expected_effective"],
                        "證據一致": evidence_matches, "一致": matches,
                        "時間毫秒": round(elapsed, 3)})
    n = len(cases)
    metrics = {
        "狀態一致": (stats["status_ok"], n),
        "欄位擷取正確": (stats["fields_ok"], stats["fields_total"]),
        "原文引用正確": (stats["sources_ok"], stats["sources_total"]),
        "判定＋基點＋生效日全對": (stats["adjustment_ok"], stats["normal_total"]),
        "異常正確分流": (stats["exception_ok"], stats["exception_total"]),
        "正常誤攔": (stats["false_positive"], stats["normal_total"]),
        "異常漏放": (stats["missed"], stats["exception_total"]),
        "無標準證據支持的引文": (stats["unsupported"], stats["claims"]),
    }
    if repeat:
        metrics["同輸入重跑一致"] = (stats["same"], n)
    return metrics, stats["ms"] / n, details


def e2e(cases):
    def payload(case):
        return {"contract": case["contract"], "report": case["annual_reports"]["2025"], "mode": "mock"}

    with TemporaryDirectory() as temporary:
        original_db = app.DB
        app.DB = Path(temporary) / "history.sqlite3"
        with app.ThreadingHTTPServer(("127.0.0.1", 0), app.Handler) as server:
            thread = Thread(target=server.serve_forever)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                def request(path, data=None):
                    with urlopen(base + path, urlencode(data).encode() if data is not None else None) as response:
                        return parse_qs(urlparse(response.url).query), response.read().decode()

                def post(path, data, marker):
                    query, page = request(path, data)
                    assert marker in page
                    return query["id"][0], page

                empty = next(case for case in cases if case["expected"] == REJECTED)
                try:
                    request("/run", payload(empty))
                except HTTPError as error:
                    assert error.code == 400 and "請提供兩份資料" in error.read().decode()
                else:
                    raise AssertionError("空文件應返回 400")
                missing = next(case for case in cases if case["title"] == "缺少必要查證")
                missing_data = payload(missing)
                pending, page = post("/run", missing_data, "待人工覆核")
                assert "<dt>利差調整bps</dt>" not in page
                returned, _ = post("/review", {"id": pending, "action": "return", "note": "已取得補件"},
                                   "已退回補件")
                missing_data.update(parent=returned, report=missing_data["report"].replace("已附查證：否", "已附查證：是"))
                corrected, _ = post("/run", missing_data, "試算完成，待確認")
                approved, page = post("/review", {"id": corrected, "action": "confirm", "approval": APPROVAL},
                                      "人工已確認試算")
                assert "2026-07-01" in page
                _, csv = request("/export?id=" + approved)
                assert all(text in csv for text in ("[MOCK MODE]", "2026-07-01", "利差調整bps,-5", "已附查證：是"))
                assert "待人工覆核" in request("/?id=" + pending)[1]
                assert "已退回補件" in request("/history")[1]
            finally:
                server.shutdown()
                thread.join()
                app.DB = original_db


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="另外執行實際模型（20 案，需要金鑰）")
    args = parser.parse_args()
    cases = json.loads((HERE / "samples_test.json").read_text(encoding="utf-8"))
    assert len(cases) == len({case["id"] for case in cases}) == 20
    assert all(set(case["annual_reports"]) == {"2024", "2025"} for case in cases)
    for case in cases:
        prior = app.run_agent(case["prior_year_contract"], case["annual_reports"]["2024"], "mock")
        assert not prior["flags"] and prior["result"]["判定"] == "達標"
    base, base_ms, base_cases = evaluate(cases, baseline, True)
    mock, mock_ms, mock_cases = evaluate(cases, lambda contract, report: assess(contract, report, "mock"), True)
    e2e(cases)
    gates = {
        "狀態一致": 1, "欄位擷取正確": .95, "原文引用正確": .95, "判定＋基點＋生效日全對": 1,
        "異常正確分流": 1, "正常誤攔": 0, "異常漏放": 0,
        "無標準證據支持的引文": 0, "同輸入重跑一致": 1,
    }
    passed = all((num / den <= gates[label] if gates[label] == 0 else num / den >= gates[label])
                 for label, (num, den) in mock.items())
    output = ["# 第四段驗收報告", "", "2025 評估年度，共 20 個獨立合成案件。另有 20 筆 2024 年度回歸檢查，均達到當年 3% 門檻，未計入此表分母。",
              "固定規則基準使用精確欄名，覆寫重複欄位，檢查必填與查證。時間只計引擎，包含模擬試算時的確認日期計算。",
              "",
              "| 指標 | 基準 | 模擬 PoC |", "|---|---:|---:|"]
    def ratio(pair):
        num, den = pair
        return f"{num}/{den} ({num/den:.1%})" if den else "無樣本"
    output.extend(f"| {name} | {ratio(base[name])} | {ratio(mock[name])} |" for name in mock)
    output.extend(["", f"平均引擎耗時：固定規則 {base_ms:.3f} ms，模擬 PoC {mock_ms:.3f} ms。",
                   "人工步驟依介面計數：預載正常案例從首頁到 CSV 需四次操作（執行、填覆核日、確認、下載）。"
                   "基準為無介面批次程式，人工步驟及人工耗時未比較。",
                   f"模擬驗收門檻：{'通過' if passed else '未通過'}。異常退回、修正、確認、CSV、舊版及空文件拒收的 HTTP 端對端測試通過。",
                   "", "## 邊界與失敗案例", "",
                   "- test-03：排放量恰為基準年的 90%，減幅等於 10% 仍達標，試算 −5 bps。",
                   "- test-09：固定規則讀出重編欄位，但沒有檢查；PoC 保留原證據並停止試算，待承辦人確認新基準。",
                   "- test-13：固定規則覆寫第一筆年度排放量；PoC 保留兩筆原文並送覆核。",
                   "- test-15：空文件應在入口拒收，避免產生空白案件版本。",
                   "- test-19：固定規則套用預設生效日；PoC 看到條款為覆核後第十五日便請承辦人查核。",
                   "", "結果只適用於合成案件。模擬擷取與基準都是規則式，差異來自異常檢查與分流，尚未測得 LLM 增益。",
                   "", "真實模型：預設未執行。"])
    target = HERE / "驗收報告.md"
    target.write_text("\n".join(output) + "\n", encoding="utf-8")
    (HERE / "驗收明細.json").write_text(json.dumps({"baseline": base_cases, "mock": mock_cases},
                                               ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.live:
        live, live_ms, live_cases = evaluate(cases, lambda contract, report: assess(contract, report, "live"), False)
        live_report = [f"平均單件引擎耗時：{live_ms:.3f} ms", *[f"{label}：{ratio(value)}" for label, value in live.items()]]
        (HERE / "真實模型驗收.json").write_text(json.dumps({"summary": live_report, "cases": live_cases},
                                                    ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(output))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
