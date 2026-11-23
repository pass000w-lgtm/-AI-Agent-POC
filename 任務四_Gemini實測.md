# 任務四｜真實 Gemini 擷取驗收

使用內建「正常達標」合成案件。在 Vercel Production 建置環境執行 `python3 smoke_gemini.py`，與產品使用同一個 `run_agent()`、Gemini 擷取、原文核對及確定性試算程式。Gemini 金鑰由 Production 環境變數提供。

| 項目 | 實測結果 |
|---|---|
| 服務及模型 | Google Gemini API 相容端點，`gemini-3.5-flash-lite` |
| 擷取值及原文證據 | 16／16 欄與標準答案、引文及行號一致 |
| 結果 | 基準排放 10,000 tCO₂e、評估年度排放 8,900 tCO₂e、目標減幅 10%；實際減幅 11%，達標，利差調整 −5 bps |
| 生效日試算 | 給定人工覆核日 2026-06-15，依合約試算 2026-07-01 生效 |
| 驗證範圍 | 一筆真實模型擷取及計算。20 個模擬案件與線上 mock 操作有各自的測試紀錄。 |

實測的 Vercel Deployment ID 為 `dpl_DwAurFARMf4wwPZs5AEtDrL2HQQN`，建置日誌保留以下驗收結果。

```text
GEMINI_SMOKE PASS gemini-3.5-flash-lite evidence=16/16 reduction=11% bps=-5 effective=2026-07-01
```

先前在同一 Vercel 專案對 Gemini 3.1 Flash‑Lite 的兩種端點均觀察到 HTTP 503。獨立測試改用 Gemini 3.5 Flash‑Lite 的相容端點後取得 HTTP 200，因此採用已實測的模型及端點。
