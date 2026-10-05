#!/usr/bin/env python3
"""K2 dentistry サイト生成スクリプト.

data/*.json と assets/ から docs/ に静的サイトを書き出す。
使い方:  python3 build.py
GitHub Pages は main ブランチの /docs フォルダを公開する設定にする。
"""
import datetime as dt
import os
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
THEME = os.environ.get("K2_THEME") or SITE.get("theme", "green")
EVENTS = json.loads((ROOT / "data/events.json").read_text(encoding="utf-8"))["events"]
GALLERY = json.loads((ROOT / "data/gallery.json").read_text(encoding="utf-8"))["photos"]
HISTORY = json.loads((ROOT / "data/history.json").read_text(encoding="utf-8"))["years"]
PEOPLE = json.loads((ROOT / "data/people.json").read_text(encoding="utf-8"))
COURSE = SITE.get("course", {"status": "closed"})
RECRUITING = COURSE.get("status") == "recruiting"
WIREFRAME = os.environ.get("K2_WIREFRAME") == "1"  # 写真が未登録の枠を見本として表示（確認用）
L = SITE["links"]

NAV = [
    ("/about/", "K2について"),
    ("/history/", "K2の歩み"),
    ("/people/", "役員・講師"),
    ("/events/", "定例会・イベント"),
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


def layout(path, title, body, depth, description=None, current=None, theme=None):
    theme = theme or THEME
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
<html lang="ja" data-theme="{theme}">
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
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Montserrat:wght@400;500&family=Noto+Serif+JP:wght@400;500;600&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap">
<link rel="stylesheet" href="{rel('/assets/style.css', depth)}">
{ga}
</head>
<body>
<a class="skip" href="#main">本文へ移動</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{rel('/', depth)}"><img class="brand-logo" src="{rel('/assets/img/mark-' + theme + '.png', depth)}" alt="K2" width="46" height="60"><span class="brand-sub">DENTISTRY</span></a>
    <nav class="nav" aria-label="メインメニュー">{nav}<a class="btn btn-primary" href="{rel('/join/', depth)}">入会案内</a></nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <div>
      <img class="foot-logo" src="{rel('/assets/img/logo-light.png', depth)}" alt="K2 DENTISTRY since 2017" width="130" height="160">
      <p>{e(SITE['full_name'])}</p>
    </div>
    <nav class="foot-nav" aria-label="フッターメニュー">
      <a href="{rel('/', depth)}">トップ</a>
      <a href="{rel('/about/', depth)}">K2について</a>
      <a href="{rel('/history/', depth)}">K2の歩み</a>
      <a href="{rel('/people/', depth)}">役員・講師紹介</a>
      <a href="{rel('/events/', depth)}">定例会・イベント</a>
      <a href="{rel('/hands-on/', depth)}">ハンズオンコース</a>
      <a href="{rel('/join/', depth)}">入会案内</a>
      {f'<a href="{e(L["instagram"])}" target="_blank" rel="noopener">Instagram</a>' if L.get("instagram") else ""}
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

VOICES = [
    ("咬合をかなりシンプルに考えられるようになり、とても臨床が楽しくなった。", "卒後10〜20年・男性歯科医師"),
    ("咬合は敷居が高いと感じる方にも、明確な理論と実際の臨床とを強く結びつけた内容でわかりやすいと思います。", "卒後20年以上・女性歯科医師"),
    ("少人数制で、とても丁寧に講義実習を進めて下さり、各受講生に理解できるように教えて下さるセミナーです。", "卒後20年以上・男性歯科医師"),
    ("クラウン1本から実践できるので、卒後間もないDrから、咬合に悩んでいるDrまで幅広くおすすめしたいです。", "卒後10〜20年・男性歯科医師"),
]


def gallery_html(d):
    photos = GALLERY[:9]
    tiles = ""
    if photos:
        for ph in photos:
            cap = f'<figcaption>{e(ph.get("caption", ""))}</figcaption>' if ph.get("caption") else ""
            tiles += f'<figure class="g-item"><img src="{rel(ph["image"], d)}" alt="{e(ph.get("alt", ph.get("caption", "")))}" loading="lazy">{cap}</figure>'
    elif L.get("instagram") and not WIREFRAME:
        return f"""<section class="section-tight">
  <div class="wrap insta-only">
    <div><p class="eyebrow">GALLERY</p><h2 class="section-title">活動の様子</h2>
    <p style="color:var(--ink-2);margin-top:12px">例会やセミナー、懇親会の様子を公式Instagramで発信しています。</p></div>
    <a class="btn btn-outline" href="{e(L['instagram'])}" target="_blank" rel="noopener">Instagram　@k2__dental</a>
  </div>
</section>"""
    elif WIREFRAME:
        for label in ["例会の様子", "講義の様子", "サマーセミナー", "懇親会", "ハンズオン実習", "忘年会"]:
            tiles += f'<figure class="g-item g-blank"><span>写真：{label}</span></figure>'
    else:
        return ""
    insta = ""
    if L.get("instagram"):
        insta = f'<a class="more" href="{e(L["instagram"])}" target="_blank" rel="noopener">Instagramでもっと見る →</a>'
    return f"""<section class="section-tight">
  <div class="wrap">
    <div class="block-head"><div><p class="eyebrow">GALLERY</p><h2 class="section-title">活動の様子</h2></div>{insta}</div>
    <div class="gallery">{tiles}</div>
  </div>
</section>"""


def course_banner(d):
    if not RECRUITING:
        return ""
    return f"""<section class="course-banner theme-navy">
  <div class="wrap">
    <div><p class="eyebrow">HANDS-ON COURSE</p><p class="cb-title">{e(COURSE.get('title', 'ハンズオンコース'))}　受講生募集中</p></div>
    <div class="btn-row">
      <a class="btn btn-light" href="{e(L['handson_form'])}" target="_blank" rel="noopener">申し込む</a>
      <a class="btn btn-ghost-light" href="{rel('/hands-on/', d)}">コースの詳細</a>
    </div>
  </div>
</section>"""


def page_home():
    path, d = "/", 0
    upcoming, _ = sort_events()
    ev_html = event_items(upcoming[:4], d) if upcoming else empty_events(d)
    news = "".join(
        f'<li><span class="news-date">{e(n["date"])}</span>'
        + (f'<a href="{rel(n["link"], d)}">{e(n["text"])}</a>' if n.get("link") else f"<span>{e(n['text'])}</span>")
        + "</li>"
        for n in SITE["news"]
    )
    body = f"""
<section class="hero-logo">
  <div class="wrap">
    <img src="{rel('/assets/img/logo-' + THEME + '.png', d)}" alt="K2 DENTISTRY since 2017" width="243" height="240">
    <h1>審美と機能を学ぶ</h1>
    <hr class="rule-gold">
    <p class="lead">桑田正博先生の咬合理論と修復治療のテクニック、そして北原信也先生の審美。1本の歯から全顎治療まで、同一のコンセプトで学ぶ歯科スタディグループです。</p>
  </div>
</section>

<section class="portraits" aria-label="名誉顧問と主宰">
  <div class="wrap">
    <figure class="portrait">
      <img src="{rel('/assets/img/portrait-kuwata.jpg', d)}" alt="桑田正博先生" width="448" height="560">
      <figcaption><span class="p-role">HONORARY ADVISER ／ 名誉顧問</span><span class="p-name">桑田正博</span><span class="p-roma">Masahiro Kuwata</span></figcaption>
    </figure>
    <figure class="portrait">
      <img src="{rel('/assets/img/portrait-kitahara.jpg', d)}" alt="北原信也先生" width="448" height="560">
      <figcaption><span class="p-role">DIRECTOR ／ 主宰</span><span class="p-name">北原信也</span><span class="p-roma">Nobuya Kitahara</span></figcaption>
    </figure>
  </div>
</section>

<section class="guide" aria-label="はじめての方へ">
  <div class="wrap">
    <p class="eyebrow" style="text-align:center">FOR NEWCOMERS</p>
    <h2 class="section-title" style="text-align:center;margin-bottom:32px">はじめての方へ</h2>
    <div class="guide-grid">
      <a class="guide-card" href="{rel('/about/', d)}"><span class="g-en">About</span><span class="g-ja">K2について</span><span class="g-tx">理念と、K.I.M・K-ing から続くなりたち</span></a>
      <a class="guide-card" href="{rel('/history/', d)}"><span class="g-en">History</span><span class="g-ja">K2の歩み</span><span class="g-tx">これまでの例会・サマーセミナーの記録</span></a>
      <a class="guide-card" href="{rel('/people/', d)}"><span class="g-en">People</span><span class="g-ja">役員・講師紹介</span><span class="g-tx">名誉顧問・主宰、役員、コース講師陣</span></a>
    </div>
  </div>
</section>

<section class="section-tight section-white">
  <div class="wrap">
    <div class="block-head"><div><p class="eyebrow">NEWS</p><h2 class="section-title">お知らせ</h2></div></div>
    <ul class="news-list">{news}</ul>
  </div>
</section>

<section class="section-tight">
  <div class="wrap">
    <div class="block-head">
      <div><p class="eyebrow">MEETINGS &amp; EVENTS</p><h2 class="section-title">定例会・イベントの予定</h2></div>
      <a class="more" href="{rel('/events/', d)}">すべての予定 →</a>
    </div>
    {ev_html}
  </div>
</section>

{course_banner(d)}

{gallery_html(d)}
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
      <a class="btn btn-primary" href="{rel('/join/', d)}">入会案内</a>
      <a class="btn btn-outline" href="{rel('/hands-on/', d)}">ハンズオンコース</a>
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


def photo_fig(ph, d, cls="h-photo"):
    return f'<figure class="{cls}"><img src="{rel(ph["image"], d)}" alt="{e(ph.get("caption", ""))}" loading="lazy" width="960" height="720"><figcaption>{e(ph.get("caption", ""))}</figcaption></figure>'


def page_about():
    path, d = "/about/", 1
    lead = PEOPLE["leaders"]
    leader_html = ""
    for p in lead:
        leader_html += f"""<div class="leader">
      <img src="{rel(p['photo'], d)}" alt="{e(p['name'])}先生" width="448" height="560" loading="lazy">
      <div class="stack"><p class="p-role">{e(p['role'])}</p><h3 class="leader-name">{e(p['name'])}<span class="p-roma">{e(p['roma'])}</span></h3>
      <p style="color:var(--ink-2)">{e(p['bio'][0])}</p><a class="more" href="{rel('/people/', d)}#{e(p['roma'].split()[-1].lower())}">プロフィールを見る →</a></div></div>"""
    story = [
        ("2007", "K.I.M-Tokyo 発足", "歯科技工士を中心に、桑田正博先生の咬合理論を学ぶ勉強会として始まりました。", None),
        ("2008", "K-ing（北原塾）発足", "北原信也先生のもとで、審美と補綴を中心に学ぶ勉強会が生まれました。", {"image": "/assets/history/2013-king-summer.jpg", "caption": "2013年 K-ing サマーセミナー"}),
        ("2017", "統合し K2 が発足", "K.I.M と K-ing が一つになり、技工の視点と審美・補綴を同じコンセプトで学ぶ場になりました。統合を機に、ハンズオンコースを新設しました。", {"image": "/assets/history/2020-kim-sokai-group.jpg", "caption": "2020年 KIM総会"}),
        ("いま", "例会・サマーセミナー・コース", "東京・八重洲での例会、毎年8月末の軽井沢サマーセミナー、年間のハンズオンコースを軸に、学生から50代まで幅広い歯科医師とコデンタルスタッフが学んでいます。", {"image": "/assets/history/2026-summer-group.jpg", "caption": "2026年 サマーセミナー"}),
    ]
    story_html = ""
    for yr, ttl, txt, ph in story:
        fig = photo_fig(ph, d) if ph else ""
        story_html += f'<li class="story-item"><div class="story-year">{yr}</div><div class="stack"><h3>{e(ttl)}</h3><p>{e(txt)}</p>{fig}</div></li>'
    body = page_head("K2について", "機能性と審美性が正しく融合した歯科医療を、同じコンセプトで学ぶスタディグループです。", "ABOUT", d) + f"""
<section class="section section-white">
  <div class="wrap split">
    <div><p class="eyebrow">CONCEPT</p><h2 class="section-title">機能性と審美性が<br>正しく融合した歯科医療</h2><p class="en-name">Academy of Tokyo-Function and Esthetic Dentistry</p></div>
    <div class="stack" style="color:var(--ink-2)">
      <p>K2は、K.I.M（Kuwata Institute Millennium）-Tokyo と K-ing（Kitahara Academy）が統合したスタディグループです。K.I.Mの目的「桑田先生の咬合理論を学び、臨床で実践し、世界に普及すること」と、K-ingの精神「よく学び、よく遊ぶ」が融合した、アットホームでありながら本質的な勉強ができる場です。</p>
      <p>私たちは、人々の健康に寄与するために歯科という分野の “Roots” を伸ばしていくことを使命と捉え、それは先人たちの築いてきた “Roots” を学び、次の時代につなげていくことだと考えています。</p>
      <p>桑田先生の教えは「無理なく・無駄なく・難しくなく」をモットーとした修復治療のベースになるもので、セミナーはそのベースを踏まえて日常臨床にすぐに活かせる内容となっています。仕事も、勉強も、遊びも、適切なバランスで。</p>
      <div class="mission-grid">
        <div class="card"><p class="card-label">MISSION 01</p><p class="card-title">桑田理論を日本から世界に発信していく</p></div>
        <div class="card"><p class="card-label">MISSION 02</p><p class="card-title">桑田イズムを継承し啓蒙する</p></div>
      </div>
    </div>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <div class="section-head"><p class="eyebrow">LEADERS</p><h2 class="section-title">名誉顧問と主宰</h2></div>
    <div class="leaders">{leader_html}</div>
  </div>
</section>
<section class="section section-white">
  <div class="wrap">
    <div class="section-head"><p class="eyebrow">STORY</p><h2 class="section-title">K2のなりたち</h2></div>
    <ol class="story">{story_html}</ol>
    <p style="margin-top:40px"><a class="btn btn-outline" href="{rel('/history/', d)}">年ごとの記録「K2の歩み」を見る</a></p>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <div class="section-head"><p class="eyebrow">ACTIVITIES</p><h2 class="section-title">活動内容</h2></div>
    <div class="program-grid">
      <div class="program"><p class="meta">2か月に1回・東京駅八重洲</p><h3>例会</h3><p>ケースプレゼンテーション（症例発表）と特別講演。Webでの同時開催もあります。コデンタルスタッフも参加できます。</p><a class="more" href="{rel('/events/', d)}">今後の予定 →</a></div>
      <div class="program"><p class="meta">毎年8月末・軽井沢</p><h3>サマーセミナー</h3><p>外部講師を招いた講演と、ご家族も参加できる懇親会。非会員の方も参加できます。</p><a class="more" href="{rel('/history/', d)}">これまでのサマーセミナー →</a></div>
      <div class="program"><p class="meta">年間コース</p><h3>ハンズオンコース</h3><p>クワタカレッジの流れを汲む実習中心のコース。F.D.O理論をはじめ、修復治療の基礎を1年で体系的に学びます。</p><a class="more" href="{rel('/hands-on/', d)}">コースについて →</a></div>
    </div>
  </div>
</section>
{cta(d)}
"""
    write(path, layout(path, "K2について", body, d, current="/about/"))


def speaker_line(sp):
    out = []
    for x in sp:
        if "（" in x:
            n, rest = x.split("（", 1)
            out.append(f"{e(n)} 先生（{e(rest)}")
        elif all(ord(c) < 128 or c == " " for c in x):
            out.append(f"{e(x)}")
        else:
            out.append(f"{e(x)} 先生")
    return "、".join(out)


def page_history():
    path, d = "/history/", 1
    years_nav = "".join(f'<a href="#y{y["year"]}">{y["year"]}</a>' for y in HISTORY)
    blocks = ""
    for y in HISTORY:
        rows = ""
        for it in y["items"]:
            sp = speaker_line(it["speakers"]) if it["speakers"] else ('<span class="tbd">講師［確認中］</span>' if it["type"] not in ("発足",) and not it["title"] else "")
            title = f'<span class="h-title">{e(it["title"])}</span>' if it["title"] else ""
            rows += f'<li><span class="h-date">{e(it["date"])}</span><span class="h-type">{e(it["type"])}</span><span class="h-body">{title}<span class="h-sp">{sp}</span></span></li>'
        photos = "".join(photo_fig(ph, d) for ph in y.get("photos", []))
        ph_html = f'<div class="h-photos">{photos}</div>' if photos else ""
        blocks += f'<section class="h-year" id="y{y["year"]}"><h2 class="h-year-num">{y["year"]}</h2><div><ul class="h-list">{rows}</ul>{ph_html}</div></section>'
    body = page_head("K2の歩み", "これまでの例会・サマーセミナー・総会の記録です。どなたが講演したかを年ごとに残しています。", "HISTORY", d) + f"""
<section class="section" style="padding-top:8px">
  <div class="wrap">
    <nav class="year-nav" aria-label="年">{years_nav}</nav>
    {blocks}
    <p class="note">記録は公式Instagramと保管写真をもとにまとめています。抜けている年や講師名、訂正があれば事務局までお知らせください。</p>
  </div>
</section>
"""
    write(path, layout(path, "K2の歩み", body, d, description="K2の例会・サマーセミナー・総会の記録（年ごとの講師と写真）", current="/history/"))


def page_people():
    path, d = "/people/", 1
    leaders = ""
    for p in PEOPLE["leaders"]:
        bio = "".join(f"<p>{e(b)}</p>" for b in p["bio"])
        leaders += f"""<article class="profile" id="{e(p['roma'].split()[-1].lower())}">
      <img src="{rel(p['photo'], d)}" alt="{e(p['name'])}先生" width="448" height="560" loading="lazy">
      <div class="stack"><p class="p-role">{e(p['role'])}</p><h2 class="leader-name">{e(p['name'])}<span class="p-roma">{e(p['roma'])}</span></h2><div class="prose" style="color:var(--ink-2)">{bio}</div></div>
    </article>"""
    def card(x, meta):
        bio = x.get("bio") or ""
        bio_html = f'<p class="person-bio">{e(bio)}</p>' if bio else '<p class="person-bio is-pending">プロフィール準備中</p>'
        return f'<div class="person">{teacher_img(x.get("photo"), x["name"], d)}<p class="person-name">{e(x["name"])} 先生</p><p class="person-meta">{e(meta)}</p>{bio_html}</div>'

    if PEOPLE.get("board"):
        board_inner = '<div class="people-grid people-light">' + "".join(card(b, b.get("role", "")) for b in PEOPLE["board"]) + "</div>"
    else:
        board_inner = '<p class="pending-note">役員の紹介は準備中です。</p>'
    lect = "".join(card(t, "／".join(t.get("topics", []))) for t in PEOPLE["lecturers"])
    body = page_head("役員・講師紹介", "K2の名誉顧問・主宰、役員、ハンズオンコースの講師陣をご紹介します。", "PEOPLE", d) + f"""
<section class="section section-white">
  <div class="wrap profiles">{leaders}</div>
</section>
<section class="section" id="board">
  <div class="wrap">
    <div class="section-head"><p class="eyebrow">BOARD</p><h2 class="section-title">K2 役員</h2><p style="margin-top:12px;color:var(--ink-2)">K2の運営（例会・サマーセミナー・懇親会など）を担う役員です。</p></div>
    {board_inner}
  </div>
</section>
<section class="section theme-navy section-night" id="course-lecturers">
  <div class="wrap">
    <div class="section-head"><p class="eyebrow">HANDS-ON COURSE LECTURERS</p><h2 class="section-title">ハンズオンコース 講師陣</h2><p class="muted-night" style="margin-top:12px">年間コースで講義・実習を担当する先生方です。コースは K2 の例会とは別の事務局で運営しています。</p></div>
    <div class="people-grid">{lect}</div>
    <p style="margin-top:40px"><a class="btn btn-light" href="{rel('/hands-on/', d)}">ハンズオンコースを見る</a></p>
  </div>
</section>
"""
    write(path, layout(path, "役員・講師紹介", body, d, current="/people/"))


def teacher_img(photo, name, d):
    if photo and photo.startswith("/"):
        return f'<img class="person-photo" src="{rel(photo, d)}" alt="{e(name)}先生" loading="lazy">'
    if photo:
        return f'<img class="person-photo" src="{rel("/assets/img/teachers/" + photo + ".jpg", d)}" alt="{e(name)}先生" loading="lazy">'
    return f'<span class="person-photo person-blank" aria-hidden="true">{e(name[0])}</span>'


def page_events():
    path, d = "/events/", 1
    upcoming, past = sort_events()
    up_html = event_items(upcoming, d) if upcoming else empty_events(d)
    past_html = ""
    if past:
        past_html = f'<div style="margin-top:64px"><h2 class="section-title" style="margin-bottom:24px">過去の開催</h2>{event_items(past, d, past=True)}</div>'
    body = page_head(
        "定例会・イベント",
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
    write(path, layout(path, "定例会・イベント", body, d, current="/events/"))


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


# 2027 年間コース（出典：2027年間コース受講生募集フライヤー）。写真は assets/img/teachers/
COURSE_2027 = [
    ("2027-04-04", "咬合理論と咬合器の基礎", [("茂野啓示", "shigeno")], None),
    ("2027-05-16", "FDO理論に基づいた咬合調整", [("園田晋平", "sonoda")], None),
    ("2027-06-13", "臼歯の機能的な形態と接触方法", [("遠山敏成", "toyama"), ("清水良介", "shimizu")], None),
    ("2027-07-25", "前歯の審美形態と支台歯形成", [("北原信也", "kitahara"), ("上林健", "kambayashi")], "懇親会"),
    ("2027-08-22", "全顎的なセットアップ方法", [("高島浩二", "takashima")], None),
    ("2027-09-26", "全顎治療におけるFDOの診査診断", [("杉山達也", None)], "症例検討会"),
]
COURSE_FEES_2027 = [("K2会員 または 卒後10年以内", "30万円"), ("一般", "40万円")]


def teacher_html(name, photo, d):
    if photo:
        img = f'<img class="avatar" src="{rel("/assets/img/teachers/" + photo + ".jpg", d)}" alt="" width="56" height="56">'
    else:
        img = f'<span class="avatar avatar-blank" aria-hidden="true">{e(name[0])}</span>'
    return f'<span class="teacher">{img}<span>{e(name)} 先生</span></span>'


def page_handson():
    path, d = "/hands-on/", 1
    items = ""
    for i, (date, theme, teachers, tag) in enumerate(COURSE_2027, 1):
        dd = dt.date.fromisoformat(date)
        badge = f'<span class="course-tag">{e(tag)}</span>' if tag else ""
        items += (
            f'<li><div><span class="course-no">{i:02d}</span><span class="course-date">{dd.month}月{dd.day}日（{WEEK[dd.weekday()]}）</span></div>'
            f'<div class="course-theme">{e(theme)}{badge}</div>'
            f'<div class="teachers">{"".join(teacher_html(n, ph, d) for n, ph in teachers)}</div></li>'
        )
    fees = "".join(f'<p>{e(k)} <span class="num">{e(v)}</span>（税込）</p>' for k, v in COURSE_FEES_2027)
    if RECRUITING:
        apply_bar = (f'<div class="cta-bar" style="margin-top:40px"><p>受講生を募集しています。お申し込み・お問い合わせは、コース事務局の申込フォームからお願いします。</p>'
                     f'<a class="btn btn-light" href="{e(L["handson_form"])}" target="_blank" rel="noopener">申込フォーム</a></div>')
    else:
        apply_bar = f'<div class="cta-bar" style="margin-top:40px"><p>{e(COURSE.get("closed_message", "受付は終了しました。"))}</p></div>'
    voices = "".join(f'<figure class="voice"><blockquote>{e(q)}</blockquote><figcaption>{e(c)}</figcaption></figure>' for q, c in VOICES)
    status_word = "受講生募集" if RECRUITING else "（受付終了）"
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
      <p>講師陣は、桑田先生の提唱した咬合理論や修復治療のテクニックを継承し実践する臨床家たちです。修復治療の大概念から F.D.O 咬合理論の真髄、審美的・機能的な要件を備えた前歯・臼歯それぞれのクラウン形態、矯正治療を含む全顎的な咬合再構成、歯牙形態を考慮した衛生管理、咬合力を視野に入れた歯内療法まで、すべてが同一コンセプトのもとに行われます。</p>
      <p>とりわけ桑田先生の咬合理論 F.D.O（Functionally Discluded Occlusion）と、審美的・機能的な要件を備えたクラウン形態については、講義に桑田先生の資料が用いられ、クワタカレッジで行われていたのと同じ内容の実習が受けられます。</p>
    </div>
  </div>
</section>
<section class="section section-night">
  <div class="wrap">
    <div class="section-head"><p class="eyebrow">2027 PROGRAM</p><h2 class="section-title">2027 年間コース　{status_word}</h2><p class="muted-night" style="margin-top:12px">咬合・補綴・審美を、深く学ぶ。全6回・日曜開催</p></div>
    <ol class="course-list">{items}</ol>
    <div class="fee-grid" style="margin-top:40px">
      <div class="fee-box"><p class="label">受講料（全6回）</p>{fees}<p class="muted-night" style="font-size:14px">※ 毎月払いが可能です。</p></div>
      <div class="fee-box"><p class="label">時間・会場</p><p>決まり次第ご案内します。</p><p class="muted-night" style="font-size:14px">参考：2026年は各回 9:30〜16:00、TT Dental Labo 2F 研修室（東京都中央区新川 2-12-14）</p></div>
    </div>
    {apply_bar}
  </div>
</section>
<section class="section"{'' if RECRUITING else ' hidden'}>
  <div class="wrap split">
    <div><p class="eyebrow">FLYER</p><h2 class="section-title">募集案内</h2><p class="lead" style="margin-top:16px">SNSやLINEでの紹介にもお使いください。</p></div>
    <img src="{rel('/assets/img/handson-2027.jpg', d)}" alt="K2 2027 年間コース 受講生募集の案内" width="1000" height="1000" style="border:1px solid var(--line)">
  </div>
</section>
<section class="section section-white" aria-label="受講者の声">
  <div class="wrap">
    <div class="section-head"><p class="eyebrow">VOICE</p><h2 class="section-title">受講者の声</h2></div>
    <div class="voice-grid">{voices}</div>
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
    write(path, layout(path, "ハンズオンコース", body, d, current="/hands-on/", theme="navy"))


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
    # 独自ドメイン：site.json の custom_domain が入っているときだけ docs/CNAME を出す
    if SITE.get("custom_domain"):
        (OUT / "CNAME").write_text(SITE["custom_domain"].strip() + "\n", encoding="utf-8")
    page_home()
    page_about()
    page_history()
    page_people()
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
