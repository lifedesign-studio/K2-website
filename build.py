#!/usr/bin/env python3
"""K2 dentistry サイト生成スクリプト.

data/*.json と assets/ から docs/ に静的サイトを書き出す。
使い方:  python3 build.py
GitHub Pages は main ブランチの /docs フォルダを公開する設定にする。
"""
import datetime as dt
import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs"
JST = dt.timezone(dt.timedelta(hours=9))
TODAY = dt.datetime.now(JST).date()
WEEK = "月火水木金土日"

SITE = json.loads((ROOT / "data/site.json").read_text(encoding="utf-8"))
EVENTS = json.loads((ROOT / "data/events.json").read_text(encoding="utf-8"))["events"]
L = SITE["links"]

NAV = [
    ("/about/", "K2について"),
    ("/events/", "イベント"),
    ("/hands-on/", "ハンズオンコース"),
]

e = html.escape


def rel(target, depth):
    """サイト内リンクを、そのページからの相対パスにする（プレビューURLと独自ドメインの両方で動くように）。"""
    if target.startswith(("http://", "https://", "mailto:", "tel:", "#")) or depth < 0:
        return target
    prefix = "../" * depth if depth else "./"
    return prefix + target.lstrip("/")


def fmt_date(s):
    d = dt.date.fromisoformat(s)
    return f"{d.year}.{d.month}.{d.day}（{WEEK[d.weekday()]}）"


def sort_events():
    ev = sorted(EVENTS, key=lambda x: x["date"])
    upcoming = [x for x in ev if dt.date.fromisoformat(x["date"]) >= TODAY]
    past = [x for x in reversed(ev) if dt.date.fromisoformat(x["date"]) < TODAY]
    return upcoming, past


def layout(path, title, body, depth, description=None, current=None):
    desc = description or SITE["description"]
    page_title = f"{title} | {SITE['name']}" if title else f"{SITE['name']} | {SITE['full_name']}"
    url = SITE["url"].rstrip("/") + path
    cur_attr = ' aria-current="page"'
    nav = "".join(
        f'<a href="{rel(href, depth)}"{cur_attr if current == href else ""}>{e(label)}</a>'
        for href, label in NAV
    )
    ga = ""
    if SITE.get("ga4_id"):
        gid = e(SITE["ga4_id"])
        ga = (
            f'<script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>'
            "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
            f"gtag('js',new Date());gtag('config','{gid}');</script>"
        )
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(page_title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(url)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(SITE['name'])}">
<meta property="og:title" content="{e(page_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{e(SITE['url'].rstrip('/') + '/assets/ogp.png')}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{rel('/assets/favicon.svg', depth)}" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@500;600;700&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap">
<link rel="stylesheet" href="{rel('/assets/style.css', depth)}">
{ga}
</head>
<body>
<a class="skip" href="#main">本文へ移動</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{rel('/', depth)}"><span class="brand-mark">K2</span><span class="brand-sub">DENTISTRY</span></a>
    <nav class="nav" aria-label="メインメニュー">{nav}<a class="btn btn-primary" href="{rel('/join/', depth)}">入会案内</a></nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <div>
      <div class="foot-brand">K2</div>
      <p>{e(SITE['full_name'])}</p>
    </div>
    <nav class="foot-nav" aria-label="フッターメニュー">
      <a href="{rel('/', depth)}">トップ</a>
      <a href="{rel('/about/', depth)}">K2について</a>
      <a href="{rel('/events/', depth)}">イベント</a>
      <a href="{rel('/hands-on/', depth)}">ハンズオンコース</a>
      <a href="{rel('/join/', depth)}">入会案内</a>
    </nav>
  </div>
  <p class="copyright">&copy; {SITE['copyright_year']} K2 All Rights Reserved.</p>
</footer>
<script>
/* 開催日を過ぎたイベントを「終了」表示にする（次回の更新までのつなぎ） */
(function(){{var t=new Date();t.setHours(0,0,0,0);
document.querySelectorAll('[data-date]').forEach(function(el){{
var d=new Date(el.getAttribute('data-date')+'T00:00:00');
if(d<t){{el.classList.add('past');var b=el.querySelector('.event-type');if(b)b.textContent='終了';}}}});}})();
</script>
</body>
</html>
"""


def write(path, content):
    target = OUT / path.lstrip("/")
    if path.endswith("/"):
        target = target / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def depth_of(path):
    return len([p for p in path.strip("/").split("/") if p]) if path.endswith("/") else path.count("/") - 1


def event_items(events, depth, past=False):
    if not events:
        return ""
    rows = []
    for x in events:
        sub = " ・ ".join(v for v in [x.get("time", ""), x.get("venue", "")] if v)
        rows.append(
            f'<li class="event-item{" past" if past else ""}" data-date="{e(x["date"])}">'
            f'<a class="event-link" href="{rel("/events/" + x["id"] + "/", depth)}">'
            f'<span class="event-date">{fmt_date(x["date"])}</span>'
            f'<span><span class="event-title">{e(x["title"])}</span><br><span class="event-sub">{e(sub)}</span></span>'
            f'<span class="event-type">{"終了" if past else e(x.get("type", "イベント"))}</span>'
            "</a></li>"
        )
    return '<ul class="event-list">' + "".join(rows) + "</ul>"


def empty_events(depth):
    return (
        '<div class="empty"><p>現在、受付中のイベントはありません。決まり次第こちらでお知らせします。</p>'
        f'<p style="margin-top:8px">年間の予定は <a href="{rel("/events/", depth)}#schedule">年間スケジュール</a> をご覧ください。</p></div>'
    )


# ---------------------------------------------------------------- pages

def page_home():
    path, d = "/", 0
    upcoming, _ = sort_events()
    ev_html = event_items(upcoming[:3], d) if upcoming else empty_events(d)
    news = "".join(
        f'<li><span class="news-date">{e(n["date"])}</span>'
        + (f'<a href="{rel(n["link"], d)}">{e(n["text"])}</a>' if n.get("link") else f"<span>{e(n['text'])}</span>")
        + "</li>"
        for n in SITE["news"]
    )
    body = f"""
<section class="hero">
  <div class="wrap split">
    <div class="stack">
      <p class="eyebrow">歯科スタディグループ K2</p>
      <h1>審美と機能を<br>学ぶ。</h1>
      <p class="lead">桑田正博先生の咬合理論と修復治療のテクニック、そして北原信也先生の審美。1本の歯から全顎治療まで、あらゆる歯科臨床を同一のコンセプトで学ぶスタディグループです。</p>
      <div class="btn-row" style="padding-top:8px">
        <a class="btn btn-primary" href="{rel('/join/', d)}">入会案内</a>
        <a class="btn btn-outline" href="{rel('/events/', d)}">イベントを見る</a>
      </div>
    </div>
    <div class="hero-panel" aria-hidden="true">
      <div class="big">K2</div>
      <p class="quote">無理なく・無駄なく・難しくなく<br><strong>よく学び、よく遊ぶ。</strong></p>
    </div>
  </div>
</section>

<section class="section-white" aria-label="K2の概要">
  <div class="wrap stats">
    <div><div class="stat-num">2018<small>年</small></div><div class="stat-label">K.I.M-Tokyo と K-ing が統合し発足</div></div>
    <div><div class="stat-num">約70<small>名</small></div><div class="stat-label">の歯科医師が在籍</div></div>
    <div><div class="stat-num">年5<small>回</small></div><div class="stat-label">症例発表会を開催</div></div>
    <div><div class="stat-num">第5<small>期</small></div><div class="stat-label">ハンズオンコース開講</div></div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head" style="display:flex;flex-wrap:wrap;justify-content:space-between;align-items:end;gap:16px">
      <div><p class="eyebrow">EVENTS</p><h2 class="section-title">今後のイベント</h2></div>
      <a class="more" href="{rel('/events/', d)}">すべてのイベント →</a>
    </div>
    {ev_html}
  </div>
</section>

<section class="section section-white" id="about">
  <div class="wrap split">
    <div><p class="eyebrow">ABOUT</p><h2 class="section-title">先人の “Roots” を学び、<br>次の時代へつなぐ。</h2></div>
    <div class="stack" style="color:var(--ink-2)">
      <p>K2は、K.I.M（Kuwata Institute Millennium）-Tokyo と K-ing（Kitahara Academy）が統合したスタディグループです。K.I.Mの目的「桑田先生の咬合理論を学び、臨床で実践し、世界に普及すること」と、K-ingの精神「よく学び、よく遊ぶ」が融合した、アットホームでありながら本質的な勉強ができる場です。</p>
      <div class="mission-grid">
        <div class="card"><p class="card-label">MISSION 01</p><p class="card-title">桑田理論を日本から世界に発信していく</p></div>
        <div class="card"><p class="card-label">MISSION 02</p><p class="card-title">桑田イズムを継承し啓蒙する</p></div>
      </div>
      <a class="more" href="{rel('/about/', d)}">K2について詳しく →</a>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><p class="eyebrow">PROGRAM</p><h2 class="section-title">学びのプログラム</h2></div>
    <div class="program-grid">
      <div class="program">
        <p class="meta">会員向け</p>
        <h3>定例会・勉強会</h3>
        <p>年5回の症例発表会と、外部講師を招いての講演会を開催。夏には軽井沢でサマーセミナーと懇親会を行い、主宰・北原信也先生によるアップデートセミナーも実施しています。</p>
        <div class="tags"><span class="tag">症例発表会 年5回</span><span class="tag">外部講師講演会</span><span class="tag">軽井沢サマーセミナー</span></div>
        <a class="more" href="{rel('/events/', d)}">イベント一覧を見る →</a>
      </div>
      <div class="program">
        <p class="meta">会員・一般どちらも受講可</p>
        <h3>K2 ハンズオンコース</h3>
        <p>桑田正博先生の「クワタカレッジ」の流れを汲む、全5回のワンデーハンズオン。F.D.O理論をはじめとする基礎知識と、実習によるスキルアップを1年で体系的に学びます。特別講師による単回コースもあります。</p>
        <div class="tags"><span class="tag">全5回・日曜開催</span><span class="tag">少人数制</span><span class="tag">単回受講可</span></div>
        <a class="more" href="{rel('/hands-on/', d)}">コース内容を見る →</a>
      </div>
    </div>
  </div>
</section>

<section class="section section-white" aria-label="受講者の声">
  <div class="wrap">
    <div class="section-head"><p class="eyebrow">VOICE</p><h2 class="section-title">受講者の声</h2></div>
    <div class="voice-grid">
      <figure class="voice"><blockquote>咬合をかなりシンプルに考えられるようになり、とても臨床が楽しくなった。</blockquote><figcaption>卒後10〜20年・男性歯科医師</figcaption></figure>
      <figure class="voice"><blockquote>咬合は敷居が高いと感じる方にも、明確な理論と実際の臨床とを強く結びつけた内容でわかりやすいと思います。</blockquote><figcaption>卒後20年以上・女性歯科医師</figcaption></figure>
      <figure class="voice"><blockquote>少人数制で、とても丁寧に講義実習を進めて下さり、各受講生に理解できるように教えて下さるセミナーです。</blockquote><figcaption>卒後20年以上・男性歯科医師</figcaption></figure>
      <figure class="voice"><blockquote>クラウン1本から実践できるので、卒後間もないDrから、咬合に悩んでいるDrまで幅広くおすすめしたいです。</blockquote><figcaption>卒後10〜20年・男性歯科医師</figcaption></figure>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap split">
    <div><p class="eyebrow">NEWS</p><h2 class="section-title">お知らせ</h2></div>
    <ul class="news-list">{news}</ul>
  </div>
</section>

{cta(d)}
"""
    write(path, layout(path, None, body, d))


def cta(d):
    return f"""<section class="cta" aria-label="ご参加の案内">
  <div class="wrap">
    <div style="max-width:34em">
      <h2>同じコンセプトで、ともに学ぶ仲間を募集しています。</h2>
      <p>歯科医師の方は入会案内を、ハンズオンコースは事務局の申込フォームをご覧ください。</p>
    </div>
    <div class="btn-row">
      <a class="btn btn-light" href="{rel('/join/', d)}">入会案内</a>
      <a class="btn btn-ghost-light" href="{rel('/hands-on/', d)}">ハンズオンコース</a>
    </div>
  </div>
</section>"""


def page_head(title, lead, eyebrow, d, crumb=None):
    bc = ""
    if crumb:
        bc = '<p class="breadcrumb">' + " / ".join(
            f'<a href="{rel(h, d)}">{e(t)}</a>' if h else e(t) for h, t in crumb
        ) + "</p>"
    lead_html = f'<p class="lead">{lead}</p>' if lead else ""
    return f'<section class="page-head"><div class="wrap">{bc}<p class="eyebrow">{eyebrow}</p><h1>{e(title)}</h1>{lead_html}</div></section>'


def page_about():
    path, d = "/about/", 1
    body = page_head("K2について", "審美と機能の融合を、歯科治療におけるグローバルな視点で学ぶスタディグループです。", "ABOUT", d) + f"""
<section class="section section-white">
  <div class="wrap split">
    <div><h2 class="section-title">初めての方へ</h2></div>
    <div class="stack" style="color:var(--ink-2)">
      <p>K2は、K.I.M（Kuwata Institute Millennium）-Tokyo と K-ing（Kitahara Academy）が統合したスタディグループです。桑田正博先生は名誉顧問を務めていらっしゃいました。</p>
      <p>K.I.Mの目的「桑田先生の咬合理論を学び、臨床で実践し、世界に普及すること」と、K-ingの精神「よく学び、よく遊ぶ」が融合した、アットホームでありながら本質的な勉強ができるセミナーです。</p>
      <p>私たちは、人々の健康に寄与するために歯科という分野の “Roots” を伸ばしていくことを使命と捉え、それは先人たちの築いてきた “Roots” を学び、時代につなげていくことだと考えています。</p>
      <p>桑田先生の教えは「無理なく・無駄なく・難しくなく」をモットーとした修復治療のベースになるもので、セミナーはそのベースを踏まえて日常臨床にすぐに活かせる内容となっています。</p>
    </div>
  </div>
</section>
<section class="section">
  <div class="wrap split">
    <div><p class="eyebrow">MISSION</p><h2 class="section-title">私たちの存在意義</h2></div>
    <div class="mission-grid">
      <div class="card"><p class="card-label">MISSION 01</p><p class="card-title">桑田理論を日本から世界に発信していく</p></div>
      <div class="card"><p class="card-label">MISSION 02</p><p class="card-title">桑田イズムを継承し啓蒙する</p></div>
    </div>
  </div>
</section>
<section class="section section-white">
  <div class="wrap split">
    <div><p class="eyebrow">HISTORY</p><h2 class="section-title">沿革</h2></div>
    <div class="stack">
      <ul class="timeline">
        <li><span class="year">2007</span><span>K.I.M（Kuwata Institute Millennium）-Tokyo 発足</span></li>
        <li><span class="year">2008</span><span>K-ing（北原塾）発足</span></li>
        <li><span class="year">2017</span><span>K-ing と K.I.M が統合</span></li>
        <li><span class="year">2018</span><span>歯科スタディグループ K2 として発足</span></li>
      </ul>
      <p style="color:var(--muted)">会員数 約70名</p>
    </div>
  </div>
</section>
{cta(d)}
"""
    write(path, layout(path, "K2について", body, d, current="/about/"))


def page_events():
    path, d = "/events/", 1
    upcoming, past = sort_events()
    up_html = event_items(upcoming, d) if upcoming else empty_events(d)
    past_html = ""
    if past:
        past_html = f'<div style="margin-top:64px"><h2 class="section-title" style="margin-bottom:24px">過去の開催</h2>{event_items(past, d, past=True)}</div>'
    body = page_head(
        "イベント",
        "定例会（症例発表会）、講演会、サマーセミナー、懇親会などのご案内です。コデンタルスタッフの方も定例会に参加できます。",
        "EVENTS", d,
    ) + f"""
<section class="section" style="padding-top:24px">
  <div class="wrap">
    <h2 class="section-title" style="margin-bottom:24px">今後の予定</h2>
    {up_html}
    {past_html}
  </div>
</section>
<section class="section section-white" id="schedule">
  <div class="wrap">
    <div class="section-head"><p class="eyebrow">SCHEDULE</p><h2 class="section-title">年間スケジュール</h2></div>
    <iframe class="calendar-frame" title="K2 年間スケジュール（Googleカレンダー）" src="{e(L['calendar_embed'])}" loading="lazy"></iframe>
    <p style="margin-top:12px;font-size:14px"><a href="{e(L['calendar_page'])}" target="_blank" rel="noopener">Googleカレンダーで開く</a></p>
  </div>
</section>
{cta(d)}
"""
    write(path, layout(path, "イベント", body, d, current="/events/"))


def page_event(x):
    path = f"/events/{x['id']}/"
    d = 2
    rows = [("日時", f"{fmt_date(x['date'])}　{e(x.get('time', ''))}")]
    venue = e(x.get("venue", ""))
    if x.get("address"):
        venue += f"<br><span style=\"color:var(--muted);font-size:14px\">{e(x['address'])}</span>"
    if x.get("map_url"):
        venue += f'<br><a href="{e(x["map_url"])}" target="_blank" rel="noopener">地図を開く</a>'
    if venue:
        rows.append(("会場", venue))
    if x.get("target"):
        rows.append(("対象", e(x["target"])))
    if x.get("fees"):
        fees = "".join(f"<li>{e(f['label'])}：{e(f['amount'])}</li>" for f in x["fees"])
        rows.append(("参加費", f'<ul class="fee-list">{fees}</ul>'))
    if x.get("deadline"):
        rows.append(("申込締切", e(x["deadline"])))
    if "walkin" in x:
        rows.append(("当日参加", "可" + (f"（{e(x['walkin_note'])}）" if x.get("walkin_note") else "") if x["walkin"] else "不可（事前申込制）"))
    if x.get("contact"):
        rows.append(("お問い合わせ", e(x["contact"])))
    table = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows)
    btns = ""
    if x.get("apply_url"):
        btns += f'<a class="btn btn-primary" href="{e(x["apply_url"])}" target="_blank" rel="noopener">{e(x.get("apply_label", "参加を申し込む"))}</a>'
    if x.get("pay_url"):
        btns += f'<a class="btn btn-outline" href="{e(x["pay_url"])}" target="_blank" rel="noopener">{e(x.get("pay_label", "参加費を支払う"))}</a>'
    paras = "".join(f"<p>{e(p)}</p>" for p in x.get("body", []))
    img = f'<img src="{rel(x["image"], d)}" alt="{e(x["title"])}のご案内" style="margin-bottom:32px;border:1px solid var(--line)">' if x.get("image") else ""
    url = SITE["url"].rstrip("/") + path
    share = (
        f'<div class="share"><span>このイベントを紹介する</span>'
        f'<a class="btn btn-outline" href="https://social-plugins.line.me/lineit/share?url={e(url)}" target="_blank" rel="noopener">LINEで送る</a>'
        f'<a class="btn btn-outline" href="https://www.facebook.com/sharer/sharer.php?u={e(url)}" target="_blank" rel="noopener">Facebookでシェア</a></div>'
    )
    body = page_head(
        x["title"], e(x.get("summary", "")), e(x.get("type", "EVENT")), d,
        crumb=[("/", "トップ"), ("/events/", "イベント"), (None, x["title"])],
    ) + f"""
<section class="section" style="padding-top:16px">
  <div class="wrap" style="max-width:880px" data-date="{e(x['date'])}">
    {img}
    <table class="detail-table">{table}</table>
    {f'<div class="btn-row" style="margin-top:32px">{btns}</div>' if btns else ''}
    {f'<div class="prose" style="margin-top:40px;color:var(--ink-2)">{paras}</div>' if paras else ''}
    <div style="margin-top:48px">{share}</div>
    <p style="margin-top:40px"><a class="more" href="{rel('/events/', d)}">← イベント一覧へ</a></p>
  </div>
</section>
"""
    write(path, layout(path, x["title"], body, d, description=x.get("summary"), current="/events/"))


def page_join():
    path, d = "/join/", 1
    body = page_head(
        "入会案内",
        "卒後間もない先生からベテランの先生まで、同じコンセプトで学ぶ仲間を募集しています。",
        "JOIN", d,
    ) + f"""
<section class="section section-white">
  <div class="wrap split">
    <div><h2 class="section-title">会員について</h2></div>
    <div class="stack">
      <table class="detail-table">
        <tr><th>歯科医師</th><td>年会費が必要です。金額は <a href="{e(L['fee_sheet'])}" target="_blank" rel="noopener">年会費一覧</a> をご覧ください。</td></tr>
        <tr><th>コデンタル<br>スタッフ</th><td>歯科衛生士・歯科技工士などのスタッフの方は、年会費なしで定例会に参加できます。</td></tr>
      </table>
      <p style="color:var(--muted);font-size:14px">サマーセミナーや懇親会は、職種を問わず別途参加費がかかります。</p>
    </div>
  </div>
</section>
<section class="section">
  <div class="wrap split">
    <div><h2 class="section-title">会員になると</h2></div>
    <ul class="timeline">
      <li><span class="year">01</span><span>年5回の症例発表会に参加できます</span></li>
      <li><span class="year">02</span><span>外部講師の講演会、北原信也先生のアップデートセミナーに参加できます</span></li>
      <li><span class="year">03</span><span>軽井沢のサマーセミナーと懇親会に参加できます</span></li>
      <li><span class="year">04</span><span>ハンズオンコースを会員価格で受講できます</span></li>
    </ul>
  </div>
</section>
<section class="section section-white">
  <div class="wrap split">
    <div><h2 class="section-title">お申し込み</h2></div>
    <div class="stack">
      <p style="color:var(--ink-2)">入会をご希望の方は、入会フォームからお申し込みください。</p>
      <div class="btn-row"><a class="btn btn-primary" href="{e(L['join_form'])}" target="_blank" rel="noopener">入会フォームを開く</a></div>
    </div>
  </div>
</section>
"""
    write(path, layout(path, "入会案内", body, d, current="/join/"))


COURSE_2026 = [
    ("01", "4月12日（日）", "咬合理論、咬合器の基礎", "茂野啓示"),
    ("02", "5月17日（日）", "FDO理論に基づいた咬合調整", "園田晋平 / 菅義嗣 / 宮澤広人"),
    ("03", "6月21日（日）", "臼歯の機能的な形態と接触方法", "遠山敏成 / 清水良介"),
    ("04", "7月12日（日）", "前歯の審美形態と支台歯形成", "北原信也 / 上林健"),
    ("05", "8月23日（日）", "全顎的なセットアップ方法", "高島浩二 / 篠原宏晨"),
]


def page_handson():
    path, d = "/hands-on/", 1
    items = "".join(
        f'<li><div><span class="course-no">{no}</span><span class="course-date">{date}</span></div>'
        f'<div class="course-theme">{e(theme)}</div><div class="course-teacher">講師：{e(t)}</div></li>'
        for no, date, theme, t in COURSE_2026
    )
    body = page_head(
        "K2 ハンズオンコース",
        "機能と審美の追求 ― 伝説のクワタカレッジを継承する総合的な臨床セミナー",
        "HANDS-ON COURSE", d,
    ) + f"""
<section class="section section-white">
  <div class="wrap split">
    <div><h2 class="section-title">コースについて</h2></div>
    <div class="stack" style="color:var(--ink-2)">
      <p>本セミナーは、金属焼付ポーセレンを開発した歯科技工士の桑田正博先生が長年主宰されていた臨床コース「クワタカレッジ」の流れを汲むハンズオンセミナーです。</p>
      <p>講師陣は、桑田先生の提唱した咬合理論や修復治療のテクニックを継承し実践する臨床家たちで、修復治療のみならず歯周治療、歯内療法、矯正治療からメインテナンスに至るまで、桑田先生の臨床コンセプトに基づきプログラムが組まれています。</p>
      <p>とりわけ、桑田先生の咬合理論 F.D.O（Functionally Discluded Occlusion）、審美的・機能的な要件を備えたクラウン形態については、講義に桑田先生の資料が用いられ、クワタカレッジで行われていたのと同じ内容の実習が受けられます。</p>
    </div>
  </div>
</section>
<section class="section section-night">
  <div class="wrap">
    <div class="section-head"><p class="eyebrow">2026 PROGRAM</p><h2 class="section-title">第5期 ハンズオンコース 2026</h2><p class="muted-night" style="margin-top:12px">全5回 桑田正博先生の教えを受けた講師陣によるワンデーハンズオン（第5期は終了しました）</p></div>
    <ol class="course-list">{items}</ol>
    <div class="fee-grid" style="margin-top:40px">
      <div class="fee-box"><p class="label">FDO咬合コース（全5回）</p><p>一般 <span class="num">300,000</span>円</p><p>K2会員 / 卒後10年以内 <span class="num">220,000</span>円</p></div>
      <div class="fee-box"><p class="label">単回K2コース</p><p>一般 <span class="num">66,000</span>円</p><p>K2会員 / 卒後10年以内 <span class="num">50,000</span>円</p></div>
      <div class="fee-box"><p class="label">時間・会場</p><p>各回 9:30〜16:00</p><p>TT Dental Labo 2F 研修室<br><span class="muted-night" style="font-size:14px">東京都中央区新川 2-12-14</span></p></div>
    </div>
    <p class="muted-night" style="margin-top:16px;font-size:14px">※ 2026年度の費用です。お支払いの分割等はご相談ください。</p>
    <div class="cta-bar" style="margin-top:40px">
      <p>2027年度（第6期）のご案内は、決まり次第こちらに掲載します。お申し込み・お問い合わせはコース事務局の申込フォームからお願いします。</p>
      <a class="btn btn-light" href="{e(L['handson_form'])}" target="_blank" rel="noopener">申込フォーム</a>
    </div>
  </div>
</section>
<section class="section">
  <div class="wrap split">
    <div><p class="eyebrow">MESSAGE</p><h2 class="section-title">コースディレクター<br>北原信也</h2></div>
    <div class="stack" style="color:var(--ink-2)">
      <p>各回ともに充実した内容で、皆さんに基礎からしっかりと学んでいただきます。</p>
      <div class="tags"><span class="tag">咬合を学ぶ</span><span class="tag">咬合は難しくない</span><span class="tag">審美と機能を学ぶ</span><span class="tag">補綴治療が変わる</span></div>
    </div>
  </div>
</section>
"""
    write(path, layout(path, "ハンズオンコース", body, d, current="/hands-on/"))


def page_404():
    # 404 はどの階層からも表示されるため、リンクはサイトのルートからの絶対パスにする
    body = """<section class="page-head"><div class="wrap"><p class="eyebrow">404</p><h1>ページが見つかりません</h1>
<p class="lead">お探しのページは移動または削除された可能性があります。</p>
<div class="btn-row" style="margin-top:28px"><a class="btn btn-primary" href="/">トップへ戻る</a><a class="btn btn-outline" href="/events/">イベント一覧</a></div></div></section>"""
    html_doc = layout("/404.html", "ページが見つかりません", body, -1)
    (OUT / "404.html").write_text(html_doc, encoding="utf-8")


# 旧Googleサイトからの転送（以前のURLをブックマークしている人向け）
REDIRECTS = {
    "/home/": "/",
    "/定例会/": "/events/",
    "/ハンズオンコース2026/": "/hands-on/",
    "/入会フォーム/": "/join/",
}


def page_redirects():
    for src, dst in REDIRECTS.items():
        d = depth_of(src)
        target = rel(dst, d)
        write(src, f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<title>移動しました | {e(SITE['name'])}</title>
<link rel="canonical" href="{e(SITE['url'].rstrip('/') + dst)}">
<meta http-equiv="refresh" content="0; url={e(target)}">
<meta name="robots" content="noindex"></head>
<body><p>このページは移動しました。<a href="{e(target)}">新しいページへ</a></p></body></html>
""")


def make_ogp():
    """共有用画像（1200×630）。assets/ogp.png が無いときだけ作る。"""
    dst = ROOT / "assets/ogp.png"
    if dst.exists():
        return
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return
    img = Image.new("RGB", (1200, 630), "#14202B")
    dr = ImageDraw.Draw(img)
    serif = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
    try:
        big = ImageFont.truetype(serif, 220, index=0)
        mid = ImageFont.truetype(serif, 54, index=0)
        small = ImageFont.truetype(serif, 30, index=0)
    except OSError:
        return
    dr.rectangle([40, 40, 1160, 590], outline="#33414F", width=2)
    dr.text((100, 90), "K2", font=big, fill="#F2F2EE")
    dr.text((104, 360), "審美と機能を学ぶ。", font=mid, fill="#F2F2EE")
    dr.text((106, 470), "歯科スタディグループ K2 ｜ K2 dentistry", font=small, fill="#D2B27A")
    img.save(dst, optimize=True)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    make_ogp()
    shutil.copytree(ROOT / "assets", OUT / "assets")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    page_home()
    page_about()
    page_events()
    for x in EVENTS:
        page_event(x)
    page_join()
    page_handson()
    page_404()
    page_redirects()
    print(f"built {sum(1 for _ in OUT.rglob('*.html'))} pages → docs/  (events: {len(EVENTS)})")


if __name__ == "__main__":
    main()
