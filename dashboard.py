"""Render a standalone zh-TW dashboard from collected GSC data; no network calls."""
import datetime as dt
import json
import math
import sys
from html import escape
from pathlib import Path
from analyze import total

METRICS = (("impressions", "曝光次數"), ("clicks", "點擊次數"),
           ("ctr", "點擊率"), ("position", "平均排名"))

def h(value):
    return escape(str(value), quote=True)

def number(value, metric):
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        return "—"
    if metric == "ctr":
        return f"{value*100:.2f}%"
    if metric == "position":
        return f"{value:.1f}"
    return f"{value:,.0f}"

def period_label(period):
    return h(period["start"]) + " ～ " + h(period["end"])

def rows_for(period, dimension):
    return period["groups"].get(dimension, {}).get("rows", [])

def cards(current, previous):
    a, b = total(current), total(previous)
    result = []
    for metric, label in METRICS:
        value = number(a.get(metric), metric) if a else "—"
        prior = number(b.get(metric), metric) if b else "—"
        delta = "資料不足"
        if a and b and isinstance(a.get(metric), (int, float)) and isinstance(b.get(metric), (int, float)):
            d = a[metric] - b[metric]
            if metric == "ctr":
                delta = f"{d*100:+.2f} 個百分點"
            elif metric == "position":
                delta = f"{d:+.1f}（越低越好）"
            else:
                delta = f"{d:+,.0f}"
        result.append(f'<article class="metric"><div class="muted">{label}</div><strong>{value}</strong>'
                      f'<small>前期 {prior} · {delta}</small></article>')
    return '<div class="metrics">' + "".join(result) + '</div>'

def dates(period):
    start = dt.date.fromisoformat(period["start"])
    end = dt.date.fromisoformat(period["end"])
    if not 0 <= (end-start).days <= 30:
        raise ValueError("Invalid period")
    return [(start+dt.timedelta(days=i)).isoformat() for i in range((end-start).days+1)]

def trend(current, previous, metric, label):
    data = {str(row["keys"][0]): row.get(metric) for p in (previous,current)
            for row in rows_for(p, "date") if row.get("keys")}
    days = dates(previous) + dates(current)
    values = [data.get(day) for day in days]
    maximum = max([v for v in values if isinstance(v,(int,float)) and math.isfinite(v) and v >= 0] + [1])
    bars = []
    for i, (day, v) in enumerate(zip(days, values)):
        known = isinstance(v,(int,float)) and math.isfinite(v) and v >= 0
        height = max(2, round(100*v/maximum)) if known else 0
        group = "prior" if i < len(dates(previous)) else "current"
        bars.append(f'<div class="day {group}" title="{h(day)}：{number(v,metric)}">'
                    f'<span class="bar-label">{number(v,metric)}</span>'
                    f'<div class="bar-track"><span class="bar" style="height:{height}%"></span></div>'
                    f'<span class="day-label">{h(day[5:])}</span></div>')
    if not any(isinstance(v,(int,float)) for v in values):
        return f'<section><h3>{label}</h3><p class="empty">尚無每日資料。</p></section>'
    return f'<section><h3>{label}</h3><div class="legend"><span>灰色：前期</span><span>藍色：本期</span></div><div class="chart-scroll"><div class="chart" style="--days:{len(days)}">' + "".join(bars) + '</div></div><p class="muted">— 表示未回傳資料，不當作零。</p></section>'

def table(rows, label, identifier):
    if not rows:
        return f'<p class="empty">目前沒有可顯示的{label}資料。</p>'
    ordered = sorted(rows, key=lambda row: (-row.get("impressions",0), -row.get("clicks",0)))
    body = []
    for row in ordered:
        key = " · ".join(str(k) for k in row.get("keys", []))
        cells = "".join(f'<td>{number(row.get(metric),metric)}</td>' for metric,_ in METRICS)
        body.append(f'<tr><th scope="row">{h(key)}</th>{cells}</tr>')
    headers = "".join(f'<th scope="col">{title}</th>' for _,title in METRICS)
    return (f'<label class="filter">搜尋{label}<input type="search" data-table="{identifier}" placeholder="輸入文字篩選"></label>'
            f'<div class="table-scroll" tabindex="0" aria-label="{label}資料"><table id="{identifier}">'
            f'<caption>依曝光排序 · 共 {len(ordered)} 筆</caption><thead><tr><th scope="col">{label}</th>{headers}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div><p class="no-match" hidden>沒有符合的項目。</p>')

CSS = """
:root{color-scheme:light dark;--bg:#f5f7fb;--panel:#fff;--ink:#172435;--muted:#526477;--line:#dce3ed;--accent:#235bcc;--prior:#9aaabd;--soft:#eaf0ff}
@media(prefers-color-scheme:dark){:root{--bg:#101622;--panel:#192332;--ink:#eef3fc;--muted:#aebdd0;--line:#344359;--accent:#89abff;--prior:#76879c;--soft:#253657}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 system-ui,-apple-system,sans-serif}
main{max-width:1100px;margin:auto;padding:24px 20px 48px}header{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;margin-bottom:18px}h1{font-size:clamp(25px,5vw,36px);line-height:1.2;margin:0}h2{font-size:20px;margin:0 0 12px}h3{font-size:16px;margin:0 0 8px}p{margin:5px 0}.muted,small,caption{color:var(--muted)}.tag{background:var(--soft);color:var(--ink);padding:5px 10px;border-radius:8px;font-size:13px}.notice{padding:12px 14px;border:1px solid var(--line);border-radius:12px;background:var(--panel);margin-bottom:16px}
nav{display:flex;gap:8px;overflow:auto;margin:12px 0 20px}nav a{white-space:nowrap;padding:8px 12px;border:1px solid var(--line);border-radius:10px;background:var(--panel);color:var(--ink);text-decoration:none}a:focus-visible,input:focus-visible,.table-scroll:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:16px}.metric,.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px}.metric strong{font-size:clamp(24px,4vw,34px);display:block;letter-spacing:-.04em;font-variant-numeric:tabular-nums;line-height:1.4}.metric small{display:block;font-size:12px}.panel{margin-bottom:16px}.trends{display:grid;grid-template-columns:1fr 1fr;gap:20px}.legend{display:flex;gap:12px;font-size:12px;color:var(--muted)}.chart-scroll,.table-scroll{overflow:auto}.chart{display:grid;grid-template-columns:repeat(var(--days),minmax(29px,1fr));align-items:end;gap:4px;min-width:420px;padding:14px 0 4px}.day{display:flex;flex-direction:column;align-items:center;font-size:10px;min-width:0}.bar-label{font-variant-numeric:tabular-nums}.bar-track{height:105px;width:72%;display:flex;align-items:flex-end}.bar{display:block;width:100%;border-radius:4px 4px 0 0;background:var(--accent)}.prior .bar{background:var(--prior)}.day-label{white-space:nowrap;color:var(--muted);font-size:10px}
.filter{display:flex;align-items:center;gap:10px;margin:8px 0 12px;color:var(--muted);flex-wrap:wrap}input{font:inherit;background:var(--bg);color:var(--ink);border:1px solid var(--line);padding:10px;border-radius:8px;min-width:0;max-width:100%}table{border-collapse:collapse;width:100%;min-width:540px;font-variant-numeric:tabular-nums}caption{text-align:left;font-size:12px;padding-bottom:8px}th,td{padding:10px 8px;border-bottom:1px solid var(--line);text-align:right}thead th{font-size:12px;color:var(--muted)}th:first-child{text-align:left;overflow-wrap:anywhere;min-width:160px;max-width:360px;font-weight:500}td{white-space:nowrap}.empty{padding:16px;background:var(--bg);border-radius:8px;color:var(--muted)}footer{font-size:12px;color:var(--muted)}.no-match{color:var(--muted)}
@media(max-width:720px){main{padding:16px 12px 32px}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.trends{grid-template-columns:1fr}.metric,.panel{padding:12px}.chart{min-width:420px}.filter input{flex:1}.metric strong{font-size:26px}}
"""
JS = """
document.querySelectorAll('[data-table]').forEach(input => {
  input.addEventListener('input', () => {
    const table = document.getElementById(input.dataset.table);
    const q = input.value.trim().toLocaleLowerCase();
    let count = 0;
    table.querySelectorAll('tbody tr').forEach(row => {
      row.hidden = !row.cells[0].textContent.toLocaleLowerCase().includes(q);
      if (!row.hidden) count++;
    });
    table.parentElement.nextElementSibling.hidden = count !== 0;
  });
});
"""

def render(report, evidence, generated=None, public=False):
    if report["property"] != evidence["property"]:
        raise ValueError("Property mismatch")
    if public and report["property"] != "sc-domain:koolo.app":
        raise ValueError("Unapproved public property")
    current, previous = report["periods"]
    stamp = generated or dt.datetime.now(dt.timezone.utc).astimezone(dt.timezone(dt.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M UTC+8")
    candidates = [c["observation"] for c in evidence["evidence_cards"] if c.get("status") == "candidate"]
    note = "公開試行 · 任何人均可查看數據。非即時資料。" if public else "報告下載版 · 非即時資料。"
    return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Crew SEO Dashboard</title><style>{CSS}</style></head>
<body><main><header><div><p class="muted">CREW / SEARCH INTELLIGENCE</p><h1>Crew SEO Dashboard</h1><p>{h(report["property"])}</p></div><span class="tag">{h(stamp)} 更新</span></header>
<div class="notice">{note}<br>本期 {period_label(current)}<br>前期 {period_label(previous)} · Google Search Console 最終 Web 搜尋資料</div>
<nav aria-label="報告導覽"><a href="#overview">總覽</a><a href="#trends">趨勢</a><a href="#queries">關鍵字</a><a href="#pages">頁面</a><a href="#opportunities">改善機會</a></nav>
<div id="overview">{cards(current,previous)}</div>
<section class="panel" id="trends"><h2>每日搜尋趨勢</h2><div class="trends">{trend(current,previous,"impressions","曝光次數")}{trend(current,previous,"clicks","點擊次數")}</div></section>
<section class="panel" id="opportunities"><h2>關鍵字改善機會</h2><p class="muted">本期曝光至少 10 次、平均排名 8～20；僅供複核，非排名預測或必改項目。</p>{table(candidates,"候選關鍵字","opportunity-table")}<p>下一步：確認實際承接頁與搜尋意圖，再決定是否調整；保留基準，14／28 天後回看。</p></section>
<section class="panel" id="queries"><h2>搜尋關鍵字</h2>{table(rows_for(current,"query"),"關鍵字","query-table")}</section>
<section class="panel" id="pages"><h2>頁面表現</h2>{table(rows_for(current,"page"),"頁面","page-table")}</section>
<footer>資料限制：關鍵字及頁面最多回傳各 1,000 筆，匿名／低量查詢可能缺漏。網站總數取自獨立查詢，不由表格加總。平均排名不是即時排名；比較不代表因果。<p>分析規則參考 SEO Coach（AK / AK SEO Labs）。</p></footer></main><script>{JS}</script></body></html>"""

def main():
    source, evidence_file, destination = map(Path, sys.argv[1:4])
    public = "--public" in sys.argv[4:]
    report = json.loads(source.read_text(encoding="utf-8"))
    evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render(report,evidence,public=public),encoding="utf-8")
    print("Dashboard generated (data not printed).")

if __name__ == "__main__":
    main()
