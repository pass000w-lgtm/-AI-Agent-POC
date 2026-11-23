"""Generate synthetic agreements, two annual texts, and predeclared answer keys."""
import json
from pathlib import Path
from random import Random

from app import CONTRACT, REPORT

HERE = Path(__file__).parent
SEED = 42
# Each row specifies the annual emissions percentage and an independently specified answer.
# Review cases have no authorized trial adjustment.
DEVELOPMENT = [
    ("開發達標", 89, "達標", ""),
    ("開發未達標", 94, "未達標", ""),
    ("開發門檻", 90, "達標", ""),
    ("開發缺查證", 90, "待覆核", "assurance"),
    ("開發缺欄", 90, "待覆核", "missing"),
]
TEST = [
    ("正常達標", 88, "達標", ""), ("正常未達標", 93, "未達標", ""),
    ("正好等於門檻", 90, "達標", ""), ("排放上限下方", 89, "達標", ""),
    ("排放上限上方", 91, "未達標", ""), ("完全減排", 0, "達標", ""),
    ("排放上升", 105, "未達標", ""), ("另訂目標及基點", 95, "達標", "alternate"),
    ("合理重編待核實", 88, "待覆核", "restated"), ("企業併購", 88, "待覆核", "merger"),
    ("盤查邊界變動", 88, "待覆核", "boundary"), ("缺少必要查證", 88, "待覆核", "assurance"),
    ("重複欄位出現不同值", 88, "待覆核", "duplicate"), ("跨文件數據矛盾", 88, "待覆核", "conflict"),
    ("空盤查文件", 88, "拒絕輸入", "empty"), ("缺年度排放欄", 88, "待覆核", "missing"),
    ("排放格式錯誤", 88, "待覆核", "format"), ("基準排放為零", 88, "待覆核", "zero"),
    ("合約生效條款不支援", 88, "待覆核", "terms"), ("合約免查證", 88, "達標", "optional"),
]
CONTRACT_KEYS = "baseline_year baseline target boundary assurance hit miss evaluation effective".split()
REPORT_KEYS = "year actual reported_boundary verified restated merger conflict".split()


def answer_fields(contract_lines, report_lines):
    evidence = {}
    for doc, keys, lines in (("合約", CONTRACT_KEYS, contract_lines),
                             ("盤查及查證摘要", REPORT_KEYS, report_lines)):
        for number, (key, line) in enumerate(zip(keys, lines), 1):
            if line:
                evidence[key] = [[line.split("：", 1)[1], f"{doc} 第{number}行", line]]
        if doc.startswith("盤查") and len(lines) > len(keys):
            line = lines[-1]
            evidence["actual"].append([line.split("：", 1)[1], f"{doc} 第{len(lines)}行", line])
    return evidence


def generate_cases():
    rng = Random(SEED)
    cases = []
    for split, scenarios in (("dev", DEVELOPMENT), ("test", TEST)):
        for index, (title, actual_pct, expected, variant) in enumerate(scenarios, 1):
            baseline = rng.randrange(81, 161) * 100
            contract = CONTRACT.replace("10000", str(baseline))
            boundary = f"範疇1+2／{split.upper()}-{index:02d}廠"
            contract = contract.replace("範疇1+2／A廠", boundary)
            prior_contract = (contract.replace("目標減幅%：10", "目標減幅%：3")
                              .replace("評估日：2026-06-15", "評估日：2025-06-15"))
            report = REPORT.replace("8900", str(baseline * actual_pct // 100)).replace("範疇1+2／A廠", boundary)
            prior = REPORT.replace("2025", "2024").replace("8900", str(baseline * 97 // 100)).replace("範疇1+2／A廠", boundary)
            hit, miss = "-5", "5"
            if variant == "alternate":
                contract = contract.replace("目標減幅%：10", "目標減幅%：5").replace("bps：-5", "bps：-7")
                hit = "-7"
            if variant == "optional":
                contract = contract.replace("要求查證：是", "要求查證：否")
            if variant in ("assurance", "optional"):
                report = report.replace("已附查證：是", "已附查證：否")
            if variant == "restated":
                report = report.replace("重編：否", "重編：是")
            if variant == "merger":
                report = report.replace("併購：否", "併購：是")
            if variant == "boundary":
                report = report.replace(boundary, boundary + "及新廠")
            if variant == "conflict":
                report = report.replace("矛盾：否", "矛盾：是")
            if variant == "duplicate":
                report += f"\n年度排放量：{baseline}"
            if variant == "missing":
                rows = report.splitlines()
                rows[1] = ""
                report = "\n".join(rows)
            if variant == "format":
                rows = report.splitlines()
                rows[1] = "年度排放量：待確認"
                report = "\n".join(rows)
            if variant == "empty":
                report = ""
            if variant == "zero":
                contract = contract.replace(f"基準排放量：{baseline}", "基準排放量：0")
            if variant == "terms":
                contract = contract.replace("覆核次月首日", "覆核後第十五日")
            cases.append(dict(
                id=f"{split}-{index:02d}", split=split, title=title,
                contract=contract, annual_reports={"2024": prior, "2025": report},
                prior_year_contract=prior_contract,
                expected=expected, expected_bps={"達標": hit, "未達標": miss}.get(expected),
                expected_effective="2026-07-01" if expected in ("達標", "未達標") else None,
                expected_evidence=answer_fields(contract.splitlines(), report.splitlines()),
            ))
    return cases


if __name__ == "__main__":
    cases = generate_cases()
    for split in ("dev", "test"):
        path = HERE / f"samples_{split}.json"
        path.write_text(json.dumps([case for case in cases if case["split"] == split],
                                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(path.name)
