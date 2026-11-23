"""Shared presentation for the local and deployed review workspaces."""

STYLE = """
:root{color-scheme:light;--navy:#122b3a;--deep:#102b39;--muted:#526876;--border:#dbe5e9;--green:#08715f;--mint:#d9f3e9;--surface:#f4f7f8;--white:#fff;--radius:15px}
*{box-sizing:border-box}
[hidden]{display:none!important}
body{margin:0;background:var(--surface);color:var(--navy);font:15px/1.6 system-ui,"Microsoft JhengHei","Noto Sans TC",sans-serif}
a{color:#076e5b;text-underline-offset:3px}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible,summary:focus-visible{outline:3px solid #329886;outline-offset:3px}
.top{background:#fff;border-bottom:1px solid var(--border)}
.top-inner{max-width:1160px;margin:auto;min-height:68px;padding:0 24px;display:flex;align-items:center;justify-content:space-between;gap:20px}
.brand{display:flex;align-items:center;gap:11px;font-weight:800;color:var(--navy);text-decoration:none;white-space:nowrap}
.brand-mark{display:grid;place-items:center;width:34px;height:34px;border-radius:10px;background:#0c6a59;color:white;font-size:12px;letter-spacing:.05em}
nav{display:flex;gap:7px;align-items:center}
nav a{white-space:nowrap;text-decoration:none;color:var(--muted);padding:8px 12px;border-radius:8px;font-weight:650;font-size:14px}
nav a:hover,nav a[aria-current=page]{background:#e9f3f0;color:#075f50}
main{max-width:1160px;margin:0 auto;padding:30px 24px 48px}
.hero{position:relative;overflow:hidden;isolation:isolate;padding:29px 32px 30px;border-radius:var(--radius);background:linear-gradient(108deg,#102b39 7%,#17454c 73%,#185d53);color:#fff;margin-bottom:22px}
.hero::before{content:"";position:absolute;z-index:-1;inset:0 0 0 56%;background:repeating-linear-gradient(0deg,transparent 0 30px,#a5e5c41c 30px 31px),repeating-linear-gradient(90deg,transparent 0 30px,#a5e5c41c 30px 31px);mask-image:linear-gradient(90deg,transparent,#000)}
.hero::after{content:"";position:absolute;z-index:-1;right:42px;top:-90px;width:360px;height:360px;border:1px solid #9ce7c14a;border-radius:50%;box-shadow:0 0 0 27px #b9eec514,0 0 0 54px #b9eec511}
.hero p{color:#c6dfdf;margin:6px 0 0;max-width:42rem}
.hero h1{font-size:clamp(24px,3.5vw,38px);line-height:1.25;margin:0;letter-spacing:-.025em}
h2{font-size:21px;line-height:1.35;margin:0}
h3{font-size:16px;line-height:1.4;margin:0}
p{margin:8px 0}
.panel{background:#fff;border:1px solid var(--border);border-radius:var(--radius);padding:22px;box-shadow:0 3px 10px #17384406;margin-bottom:17px}
.head{display:flex;justify-content:space-between;align-items:start;gap:16px;margin-bottom:14px}
.note{color:var(--muted);font-size:13px;line-height:1.5;margin:5px 0 0;display:block}
.controls,.docs,.review-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.controls{gap:20px 16px}
label,.label{display:block;font-weight:700}
label>input,label>select,label>textarea,label+select{margin-top:6px}
select,input[type=password],input[type=date],input[type=text],textarea{display:block;border:1px solid #c3d2d9;border-radius:9px;background:#fff;color:var(--navy);font:inherit;padding:9px 11px;width:100%}
select:disabled{opacity:.6}
.doc{background:#f8fafb;border:1px solid var(--border);border-radius:11px;padding:14px;min-width:0}
textarea{min-height:218px;resize:vertical;font:13px/1.65 ui-monospace,"Cascadia Mono","Microsoft JhengHei",monospace;background:white}
.file{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:10px;font-size:13px;font-weight:650}
.file input{margin:0;max-width:100%;color:var(--muted);font-size:12px}
.file input::file-selector-button{border:1px solid #c4d5dc;border-radius:7px;background:#fff;padding:5px 8px;margin-right:8px;color:var(--navy);cursor:pointer}
.actions{display:flex;align-items:center;flex-wrap:wrap;gap:10px;margin-top:14px}
button,.button{border:1px solid transparent;border-radius:8px;background:var(--green);color:#fff;padding:9px 13px;min-height:39px;font:650 14px/1.25 system-ui,sans-serif;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;justify-content:center;gap:5px}
button:hover,.button:hover{background:#075d50}
button:disabled{cursor:wait;opacity:.6}
button.secondary,.button.secondary{background:#fff;color:var(--navy);border-color:#c5d4da}
button.secondary:hover,.button.secondary:hover{background:#eff5f6}
.trial{margin-top:15px;padding:12px;background:#f1f7f5;border:1px solid #dbece5;border-radius:9px}
.trial input{max-width:320px}
.assist{margin-top:14px;padding-top:12px;border-top:1px solid var(--border);display:flex;align-items:center;flex-wrap:wrap;gap:6px 14px}
.assist .note{margin:0}
.status{font-size:13px;color:#075e50;display:block;margin:6px 0 0}
.status:empty{display:none}
.pill{display:inline-flex;align-items:center;padding:4px 9px;border-radius:999px;background:#edf3f6;color:#355060;font-size:12px;font-weight:750;white-space:nowrap}
.pill.good{background:#e1f3ec;color:#075b4c}.pill.warn{background:#fff1d9;color:#795019}
.meta{color:var(--muted);font-size:13px;overflow-wrap:anywhere}
.metrics{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin:15px 0 0}
.metrics>div{padding:10px 13px;border-radius:10px;background:#f0f6f5;border:1px solid #deebe7;min-width:0}
dt{font-size:13px;color:#47656b;font-weight:650}
dd{margin:4px 0 0;font-size:17px;font-weight:780;overflow-wrap:anywhere}
.flags{padding:9px 12px 9px 32px;border-radius:9px;background:#fff5e5;color:#714a1e}
details.panel{padding:16px 22px}
summary{font-weight:750;cursor:pointer}
details .note{margin-bottom:12px}
details form[data-assessment] .panel{box-shadow:none;margin-bottom:9px}
.review-grid{margin-top:12px}
.review-grid input{min-height:42px}
.scroll{overflow:auto}
table{width:100%;border-collapse:collapse;text-align:left}
th,td{text-align:left;border-bottom:1px solid var(--border);padding:9px 8px;vertical-align:top;overflow-wrap:anywhere}
thead th{font-size:13px;color:var(--muted)}
.steps{padding-left:24px;margin:14px 0 0}
.steps li{padding:0 0 13px 6px}
.steps li::marker{color:var(--green);font-weight:750}
.history tr:last-child td{border-bottom:0}
@media(max-width:730px){.top-inner{align-items:flex-start;flex-direction:column;gap:6px;padding:12px 16px}.top-inner nav{width:100%;gap:3px}nav a{padding:7px 9px}main{padding:18px 14px 30px}.hero,.panel{padding:17px}.controls,.docs,.review-grid{grid-template-columns:1fr}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.hero::after{right:-110px}.head{gap:9px;flex-wrap:wrap}textarea{min-height:180px}}
"""

GUIDE = """
<section class="panel">
    <div class="head"><div><h2>批次驗收</h2><p class="note">即時重跑 20 個獨立合成案件，查看判定一致率、異常分流與失敗案例。全程使用 [MOCK MODE]。</p></div>
    <form method="post" action="/verification"><button type="submit">一鍵跑 20 案模擬驗收</button></form></div>
</section>

<section class="panel" aria-labelledby="guide-start">
    <div class="head"><div><h2 id="guide-start">第一次使用：正常案件</h2><p class="note">用免金鑰的內建文件，走完一次分析與覆核。</p></div><a class="button" href="/?sample=正常達標">載入正常達標案例</a></div>
    <ol class="steps">
        <li><strong>選擇案例與擷取模式</strong><p>在「示範案件」選正常達標，模式保持 [MOCK MODE]。表單會填入授信合約與盤查及查證摘要。</p></li>
        <li><strong>執行履約評估</strong><p>檢查結果是否為達標、減幅 11%、利差調整 −5 bps，再展開「查看原文證據」核對數值和行號。</p></li>
        <li><strong>人工覆核並下載</strong><p>輸入覆核日期 2026-06-15，點「確認試算」，生效日應為 2026-07-01。下載 CSV，或從「履約紀錄」回看該版本。</p></li>
    </ol>
</section>
<section class="panel" aria-labelledby="guide-exception">
    <div class="head"><div><h2 id="guide-exception">進階測試：缺查證案件</h2><p class="note">確認缺件時會暫緩利差試算，補件後才重新評估。</p></div><a class="button secondary" href="/?sample=缺查證">載入缺查證案例</a></div>
    <ol class="steps">
        <li>選缺查證並執行，預期顯示「待人工覆核」。</li>
        <li>填寫覆核備註，點「退回補件」。</li>
        <li>展開「修正資料並重跑」，將合成摘要的「已附查證：否」改為「已附查證：是」，重新執行。可用「上一版本」回查變更前結果。</li>
    </ol>
</section>
<section class="panel">
    <h2>其他測試方式</h2>
    <div class="controls">
        <div><h3>生成隨機文件</h3><p class="note">一鍵填入一組新的合成合約與盤查摘要，可下載兩份 TXT，適合練習資料匯入與不同案件判定。</p></div>
        <div><h3>使用實際模型</h3><p class="note">選「實際模型（Gemini）」並在正式站輸入試用碼，再送出一組合成文件。結果會顯示模型名稱與來源。請使用教學合成資料。</p></div>
    </div>
</section>
"""
