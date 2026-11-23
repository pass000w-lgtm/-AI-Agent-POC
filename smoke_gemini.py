"""Run one real Gemini extraction with the built-in synthetic sample."""
from app import CONTRACT, FIELDS, REPORT, calculate, live_configuration, run_agent


def main():
    provider, key, model = live_configuration()
    if provider != "Gemini" or not key:
        raise SystemExit("Gemini 驗收需要 GEMINI_API_KEY。")
    expected = run_agent(CONTRACT, REPORT, "mock")
    try:
        observed = run_agent(CONTRACT, REPORT, "live")
    except ValueError as error:
        raise SystemExit(f"Gemini 驗收失敗：{error}") from None
    matched = sum(observed["evidence"][field] == expected["evidence"][field] for field in FIELDS)
    if matched != len(FIELDS) or observed["result"] != expected["result"]:
        raise SystemExit(f"Gemini 驗收失敗：欄位與證據符合 {matched}/{len(FIELDS)}。")
    confirmed = calculate(observed["fields"], approval="2026-06-15")
    if confirmed["生效日"] != "2026-07-01":
        raise SystemExit("Gemini 驗收失敗：生效日與預期不符。")
    print(f"GEMINI_SMOKE PASS {model} evidence={matched}/{len(FIELDS)} "
          f"reduction={confirmed['減幅%']}% bps={confirmed['利差調整bps']} effective={confirmed['生效日']}")


if __name__ == "__main__":
    main()
