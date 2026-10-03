#!/usr/bin/env python3
"""GiftScope static site generator (stdlib only).

python3 tools/build.py  ->  dist/
Data: data/products.json (tools/make_products.py) + data/site.json
"""
import datetime as dt
import html
import json
import math
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
SRC = ROOT / "src"
SITE = json.load(open(ROOT / "data" / "site.json"))
DB = json.load(open(ROOT / "data" / "products.json"))
P = DB["products"]
TAG = "giftscope-20"
DOMAIN = SITE["domain"]
CHECKED = dt.date.fromisoformat(DB["checked"])
CHECKED_TXT = f"{CHECKED:%b} {CHECKED.day}, {CHECKED.year}"
AGES = SITE["ages"]
THEMES = SITE["themes"]
BUDGETS = SITE["budgets"]
GUIDES = json.load(open(ROOT / "data" / "guides.json"))["guides"]
THEME = {t["slug"]: t for t in THEMES}
E = html.escape
PAGES = []  # for sitemap


def _ver(rel):
    import hashlib
    return hashlib.md5((SRC / rel).read_bytes()).hexdigest()[:8]


# cache-busting: /assets/* is cached for a week, so every CSS/JS URL carries its content hash
ASSET_V = {f"/{r}": f"/{r}?v={_ver(r)}" for r in ("assets/css/site.css", "assets/js/app.js", "assets/js/finder.js")}


# ---------- product helpers ----------
def age_groups(p):
    lo, hi = p["age_min"], p["age_max"]
    if lo == 0 and hi == 1:
        hi = 0
    out = []
    for g in AGES:
        if g["slug"] == "teens":
            if hi >= 13 and lo >= 6:
                out.append("teens")
        elif lo <= g["max"] and hi >= g["min"]:
            out.append(g["slug"])
    return out


def budget_of(p):
    for b in BUDGETS:
        if b["min"] <= p["price"] <= b["max"]:
            return b["slug"]
    raise ValueError(p)


def score(p):
    s = (p["rating"] * p["reviews"] + 4.3 * 800) / (p["reviews"] + 800)
    return round(s + (0.12 if p["top"] else 0), 4)


for p in P:
    p["ages"] = age_groups(p)
    p["budget"] = budget_of(p)
    p["score"] = score(p)
    if not p["ages"]:
        raise SystemExit(f"no age group: {p['name']}")


def img(i, size=500):
    return f"https://m.media-amazon.com/images/I/{i}._AC_SL{size}_.jpg"


def money(x):
    return f"${x:,.2f}"


def age_label(p):
    lo, hi = p["age_min"], p["age_max"]
    if lo == 0 and hi <= 1:
        return "0–12 mo"
    if hi >= 99:
        return f"{lo}+"
    return f"{lo}–{hi}"


def reviews_txt(n):
    return f"{n/1000:.1f}K".replace(".0K", "K") if n >= 1000 else str(n)


def ranked(items):
    return sorted(items, key=lambda p: -p["score"])


# ---------- layout ----------
ICON = '<svg viewBox="0 0 32 32" aria-hidden="true"><rect x="4" y="13" width="24" height="15" rx="2.5" fill="currentColor"/><rect x="2.5" y="9" width="27" height="6" rx="2" fill="currentColor" opacity=".85"/><rect x="14.5" y="9" width="3" height="19" fill="#fff" opacity=".9"/><path d="M16 9c-2-5-8-6-8-2.5S13 9 16 9zm0 0c2-5 8-6 8-2.5S19 9 16 9z" fill="none" stroke="currentColor" stroke-width="2"/></svg>'

NAV = [("/gift-finder/", "Gift Finder"), ("/guides/", "Guides"), ("/age/", "By Age"), ("/interest/", "By Interest"),
       ("/budget/", "By Budget"), ("/all-gifts/", "All Gifts")]


def header(active):
    cur = ' aria-current="page"'
    links = "".join(f'<a href="{u}"{cur if active == u else ""}>{t}</a>' for u, t in NAV)
    return f"""<a class="skip" href="#main">Skip to content</a>
<header class="top">
 <div class="wrap top__in">
  <a class="logo" href="/">{ICON}<span>Gift<b>Scope</b></span></a>
  <button class="menu-btn" type="button" aria-expanded="false" aria-controls="nav" data-menu>Menu</button>
  <nav id="nav" class="nav" aria-label="Main">{links}</nav>
 </div>
</header>"""


FOOTER = f"""<footer class="foot">
 <div class="wrap foot__grid">
  <div><a class="logo logo--foot" href="/">{ICON}<span>Gift<b>Scope</b></span></a>
   <p>{E(SITE["tagline"])}</p>
   <p class="small">Part of the <a href="https://scooters.specversus.com/">SpecVersus</a> family of buying guides.</p></div>
  <div><h2>By age</h2>{''.join(f'<a href="/age/{g["slug"]}/">{E(g["label"])} <span>({g["range"]})</span></a>' for g in AGES)}</div>
  <div><h2>By budget</h2>{''.join(f'<a href="/budget/{b["slug"]}/">{E(b["title"])}</a>' for b in BUDGETS)}</div>
  <div><h2>Gift guides</h2>{''.join(f'<a href="/guides/{g["slug"]}/">{E(g["title"])}</a>' for g in GUIDES)}</div>
  <div><h2>GiftScope</h2><a href="/gift-finder/">Gift Finder</a><a href="/guides/">All gift guides</a><a href="/about/">About</a><a href="/disclosure/">Affiliate disclosure</a><a href="/privacy/">Privacy</a></div>
 </div>
 <div class="wrap foot__legal">
  <p><strong>As an Amazon Associate I earn from qualifying purchases.</strong> Links to Amazon.com are affiliate links: we may earn a commission at no extra cost to you.</p>
  <p>Prices and ratings were checked on Amazon.com on {CHECKED_TXT} and can change at any time; the price shown on Amazon at the time of purchase applies. Product images are served by Amazon. Amazon and the Amazon logo are trademarks of Amazon.com, Inc. or its affiliates. Brand and character names belong to their owners; GiftScope is not affiliated with them.</p>
  <p>© {dt.date.today().year} GiftScope</p>
 </div>
</footer>"""


PIN_META = f'\n<meta name="p:domain_verify" content="{E(SITE["pinterest_verify"])}"/>' if SITE.get("pinterest_verify") else ""


def page(path, title, desc, body, active="", jsonld=None, og=None, extra=""):
    canonical = DOMAIN + path
    ld = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (jsonld or []))
    ogi = f'<meta property="og:image" content="{E(og)}">' if og else ""
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">{PIN_META}
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website"><meta property="og:site_name" content="GiftScope">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{canonical}">{ogi}
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1f5c4a">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="preconnect" href="https://m.media-amazon.com">
<link rel="stylesheet" href="/assets/css/site.css">
{ld}{extra}
</head>
<body>
{header(active)}
<main id="main">
{body}
</main>
{FOOTER}
<script src="/assets/js/app.js" defer></script>
</body>
</html>
"""
    for a, v in ASSET_V.items():
        doc = doc.replace(f'"{a}"', f'"{v}"')
    out = DIST / path.lstrip("/") / "index.html" if path.endswith("/") else DIST / path.lstrip("/")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc)
    if path != "/404.html":
        PAGES.append(path)


def crumbs(items):
    links = " <span aria-hidden=\"true\">›</span> ".join(
        f'<a href="{u}">{E(t)}</a>' if u else f'<span aria-current="page">{E(t)}</span>' for u, t in items)
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": t, **({"item": DOMAIN + u} if u else {})}
        for i, (u, t) in enumerate(items)]}
    return f'<nav class="crumbs" aria-label="Breadcrumb">{links}</nav>', ld


# ---------- components ----------
def card(p, rank=None):
    th = THEME[p["theme"]]
    rk = f'<span class="card__rank">#{rank}</span>' if rank else ""
    pick = '<span class="card__pick">Top pick</span>' if p["top"] else ""
    return f"""<article class="card" data-ages="{' '.join(p['ages'])}" data-theme="{p['theme']}" data-budget="{p['budget']}" data-price="{p['price']}" data-score="{p['score']}" data-reviews="{p['reviews']}">
 <a class="card__media" href="{E(p['url'])}" target="_blank" rel="sponsored nofollow noopener" tabindex="-1" aria-hidden="true">{rk}{pick}<img src="{img(p['image'])}" alt="" loading="lazy" decoding="async" width="500" height="500"></a>
 <div class="card__body">
  <p class="card__meta"><span class="chip-age">Ages {age_label(p)}</span><span>{th['emoji']} {E(th['label'])}</span></p>
  <h3 class="card__title"><a href="{E(p['url'])}" target="_blank" rel="sponsored nofollow noopener">{E(p['name'])}</a></h3>
  <p class="card__blurb">{E(p['blurb'])}</p>
  <p class="card__rating"><span class="stars" style="--r:{p['rating']}" aria-hidden="true"></span><span>{p['rating']:.1f}</span><span class="muted">({reviews_txt(p['reviews'])} ratings)</span></p>
  <div class="card__buy"><span class="price">{money(p['price'])}<sup>*</sup></span><a class="btn btn--amz" href="{E(p['url'])}" target="_blank" rel="sponsored nofollow noopener">See on Amazon</a></div>
 </div>
</article>"""


def filters(skip):
    groups = []
    if skip != "age":
        groups.append(("age", "Age", [(g["slug"], g["short"] if g["slug"] != "baby" else "Baby") for g in AGES]))
    if skip != "theme":
        groups.append(("theme", "Interest", [(t["slug"], t["label"]) for t in THEMES]))
    if skip != "budget":
        groups.append(("budget", "Budget", [(b["slug"], b["label"]) for b in BUDGETS]))
    out = []
    for key, label, opts in groups:
        chips = "".join(f'<button type="button" class="fchip" data-f="{key}" data-v="{v}" aria-pressed="false">{E(t)}</button>' for v, t in opts)
        out.append(f'<div class="fgroup"><span class="fgroup__label">{label}</span><div class="fgroup__chips">{chips}</div></div>')
    return f"""<div class="filters" data-filters>
 {''.join(out)}
 <div class="fbar"><label>Sort <select data-sort><option value="score">Top rated</option><option value="price-asc">Price: low to high</option><option value="price-desc">Price: high to low</option><option value="reviews">Most reviewed</option></select></label>
 <span class="fcount" data-count aria-live="polite"></span><button type="button" class="link-btn" data-clear hidden>Clear filters</button></div>
</div>"""


def note():
    return f'<p class="pnote">*Prices checked on Amazon.com on {CHECKED_TXT}. Prices change often, especially around Black Friday; check Amazon for the current price.</p>'


def item_list(name, items):
    return {"@context": "https://schema.org", "@type": "ItemList", "name": name,
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": p["name"], "url": p["url"]}
                                for i, p in enumerate(items[:30])]}


def listing(path, crumb_items, h1, intro, items, skip, emoji="", related=""):
    items = ranked(items)
    cr, cld = crumbs(crumb_items)
    lo, hi = min(p["price"] for p in items), max(p["price"] for p in items)
    body = f"""<section class="phead"><div class="wrap">{cr}
 <h1>{f'<span class="phead__emoji" aria-hidden="true">{emoji}</span>' if emoji else ''}{E(h1)}</h1>
 <p class="lead">{E(intro)}</p>
 <p class="phead__facts"><span>{len(items)} gift ideas</span><span>{money(lo)} – {money(hi)}</span><span>Rated 4.3★ and up</span><span>Updated {CHECKED_TXT}</span></p>
 <p class="disclose">We may earn a commission from Amazon links, at no extra cost to you.</p>
 <a class="btn btn--ghost" href="/gift-finder/">Not sure? Try the 30-second Gift Finder →</a>
</div></section>
<section class="wrap list-wrap">
 {filters(skip)}
 <div class="grid" data-grid>{''.join(card(p, i + 1) for i, p in enumerate(items))}</div>
 <p class="empty" data-empty hidden>No gifts match those filters. <button type="button" class="link-btn" data-clear>Clear filters</button></p>
 {note()}
</section>
{related}"""
    title = f"{h1} ({CHECKED:%Y}) | GiftScope"
    desc = f"{intro[:150].rsplit(' ', 1)[0]}… {len(items)} top-rated ideas from {money(lo)}."
    page(path, title, desc, body, active=crumb_items[1][0] if len(crumb_items) > 2 else "",
         jsonld=[item_list(h1, items), cld], og=img(items[0]["image"], 1000))


def tiles_age(cls=""):
    return f'<div class="tiles tiles--age {cls}">' + "".join(
        f'<a class="tile" href="/age/{g["slug"]}/"><span class="tile__emoji" aria-hidden="true">{g["emoji"]}</span><span class="tile__big">{g["short"]}</span><span class="tile__lbl">{E(g["label"])}</span><span class="tile__n">{sum(g["slug"] in p["ages"] for p in P)} ideas</span></a>'
        for g in AGES) + "</div>"


def tiles_theme():
    return '<div class="tiles tiles--theme">' + "".join(
        f'<a class="tile tile--theme" href="/interest/{t["slug"]}/"><span class="tile__emoji" aria-hidden="true">{t["emoji"]}</span><span class="tile__lbl">{E(t["label"])}</span><span class="tile__n">{sum(p["theme"] == t["slug"] for p in P)}</span></a>'
        for t in THEMES) + "</div>"


def pills_budget():
    return '<div class="pills">' + "".join(
        f'<a class="pill" href="/budget/{b["slug"]}/"><b>{E(b["label"])}</b><span>{sum(p["budget"] == b["slug"] for p in P)} gifts</span></a>'
        for b in BUDGETS) + "</div>"


def related_block(title, inner):
    return f'<section class="band band--soft"><div class="wrap"><h2 class="h2">{E(title)}</h2>{inner}</div></section>'


# ---------- pages ----------
def build_home():
    tops = ranked([p for p in P if p["top"]])[:12]
    HI, LZ = 'fetchpriority="high"', 'loading="lazy"'
    hero_imgs = "".join(f'<li style="--i:{i}"><img src="{img(p["image"], 400)}" alt="" width="200" height="200" {HI if i < 2 else LZ}></li>' for i, p in enumerate(tops[:6]))
    body = f"""<section class="hero">
 <div class="wrap hero__in">
  <div class="hero__copy">
   <p class="eyebrow">Holiday Gift Guide {CHECKED:%Y}</p>
   <h1>Find the gift they'll <em>actually</em> play with.</h1>
   <p class="lead">{len(P)} top-rated gift ideas for babies to teens, hand-picked from Amazon best sellers and sorted by age, interest and budget.</p>
   <div class="hero__cta"><a class="btn btn--primary btn--lg" href="/gift-finder/">Start the Gift Finder</a><a class="btn btn--ghost btn--lg" href="/all-gifts/">Browse all gifts</a></div>
   <p class="hero__note">3 quick questions · no sign-up · results in 30 seconds</p>
  </div>
  <ul class="hero__stack" aria-hidden="true">{hero_imgs}</ul>
 </div>
</section>
<section class="band"><div class="wrap">
 <div class="sec-head"><h2 class="h2">Shop by age</h2><a href="/age/">All ages →</a></div>
 {tiles_age()}
</div></section>
<section class="band band--soft"><div class="wrap">
 <div class="sec-head"><h2 class="h2">Shop by interest</h2><a href="/interest/">All interests →</a></div>
 {tiles_theme()}
</div></section>
<section class="band"><div class="wrap">
 <div class="sec-head"><h2 class="h2">Top picks this season</h2><a href="/all-gifts/">See all {len(P)} →</a></div>
 <div class="grid">{''.join(card(p) for p in tops)}</div>
 {note()}
</div></section>
<section class="band band--soft"><div class="wrap">
 <div class="sec-head"><h2 class="h2">Gift guides</h2><a href="/guides/">All guides →</a></div>
 {guide_tiles()}
</div></section>
<section class="band band--pine"><div class="wrap">
 <div class="sec-head"><h2 class="h2">Shop by budget</h2></div>
 {pills_budget()}
</div></section>
<section class="band"><div class="wrap how">
 <h2 class="h2">How we pick</h2>
 <ol class="how__list">
  <li><b>Start with what kids want.</b> We scan Amazon's toy best-seller lists by category, then the most-searched themes: superheroes, dinosaurs, LEGO, STEM and more.</li>
  <li><b>Keep only proven gifts.</b> Every pick has a strong rating (4.3★ or higher) from real buyers. We skip knock-offs, resale bundles and items with too few reviews.</li>
  <li><b>Sort by what you know.</b> Age, interest and budget, so you can find a great gift in a minute, even for a kid you don't see often.</li>
 </ol>
</div></section>"""
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": "GiftScope", "url": DOMAIN + "/",
           "description": SITE["tagline"]}, item_list("Top gift picks", tops)]
    page("/", f"GiftScope: Best Gifts for Kids {CHECKED:%Y} by Age, Interest & Budget",
         f"Find the perfect gift fast: {len(P)} top-rated toy and gift ideas for babies, kids and teens, sorted by age, interest and budget. Try the 30-second Gift Finder.",
         body, active="/", jsonld=ld, og=img(tops[0]["image"], 1000))


def build_hubs():
    for path, title, h1, lead, inner in [
        ("/age/", "Gift Ideas by Age: Babies to Teens | GiftScope", "Gifts by age",
         "Pick an age to see gifts that match their stage, from first play gyms to teen tech.", tiles_age()),
        ("/interest/", "Gift Ideas by Interest | GiftScope", "Gifts by interest",
         "What are they into? Choose a theme to see the best-rated gifts for it.", tiles_theme()),
        ("/budget/", "Gift Ideas by Budget | GiftScope", "Gifts by budget",
         "From stocking stuffers under $10 to big gifts over $100.", pills_budget()),
    ]:
        cr, cld = crumbs([("/", "Home"), (None, h1)])
        body = f'<section class="phead"><div class="wrap">{cr}<h1>{h1}</h1><p class="lead">{lead}</p></div></section><section class="band"><div class="wrap">{inner}</div></section>'
        page(path, title, lead, body, active=path, jsonld=[cld])


def build_listings():
    for g in AGES:
        items = [p for p in P if g["slug"] in p["ages"]]
        others = "".join(f'<a class="pill pill--sm" href="/age/{o["slug"]}/"><b>{o["emoji"]} {E(o["label"])}</b><span>{o["range"]}</span></a>' for o in AGES if o is not g)
        listing(f"/age/{g['slug']}/", [("/", "Home"), ("/age/", "By Age"), (None, g["label"])],
                g["title"], g["intro"], items, "age", g["emoji"],
                related_block("Other ages", f'<div class="pills">{others}</div>'))
    for t in THEMES:
        items = [p for p in P if p["theme"] == t["slug"]]
        listing(f"/interest/{t['slug']}/", [("/", "Home"), ("/interest/", "By Interest"), (None, t["label"])],
                t["title"], t["intro"], items, "theme", t["emoji"], related_block("More interests", tiles_theme()))
    for b in BUDGETS:
        items = [p for p in P if p["budget"] == b["slug"]]
        listing(f"/budget/{b['slug']}/", [("/", "Home"), ("/budget/", "By Budget"), (None, b["label"])],
                b["title"], b["intro"], items, "budget", "", related_block("Other budgets", pills_budget()))
    cr = [("/", "Home"), (None, "All Gifts")]
    listing("/all-gifts/", cr, "All Gift Ideas",
            "Every gift on GiftScope in one place. Filter by age, interest and budget, or sort by price and ratings.",
            P, "", "🎁")


def build_finder():
    data = [{"n": p["name"], "u": p["url"], "i": p["image"], "a": p["ages"], "t": p["theme"], "b": p["budget"],
             "p": p["price"], "r": p["rating"], "c": p["reviews"], "s": p["score"], "g": age_label(p), "d": p["blurb"]}
            for p in P]
    ages = "".join(f'<button type="button" class="opt" data-q="age" data-v="{g["slug"]}"><span class="opt__emoji" aria-hidden="true">{g["emoji"]}</span><b>{E(g["label"])}</b><small>{g["range"]}</small></button>' for g in AGES)
    themes = "".join(f'<button type="button" class="opt opt--sm" data-q="theme" data-v="{t["slug"]}" aria-pressed="false"><span class="opt__emoji" aria-hidden="true">{t["emoji"]}</span><b>{E(t["label"])}</b></button>' for t in THEMES)
    budgets = "".join(f'<button type="button" class="opt" data-q="budget" data-v="{b["slug"]}"><b>{E(b["label"])}</b></button>' for b in BUDGETS) + \
        '<button type="button" class="opt" data-q="budget" data-v="any"><b>Any budget</b></button>'
    cr, cld = crumbs([("/", "Home"), (None, "Gift Finder")])
    body = f"""<section class="phead phead--finder"><div class="wrap">{cr}
 <h1>Gift Finder</h1>
 <p class="lead">Answer 3 quick questions and get a short list of top-rated gifts that fit.</p>
</div></section>
<section class="wrap finder" data-finder>
 <ol class="steps" aria-label="Progress"><li data-step-dot="1" class="is-on">Age</li><li data-step-dot="2">Interests</li><li data-step-dot="3">Budget</li><li data-step-dot="4">Your gifts</li></ol>
 <div class="qstep" data-step="1"><h2 class="qtitle">Who is the gift for?</h2><div class="opts opts--age">{ages}</div></div>
 <div class="qstep" data-step="2" hidden><h2 class="qtitle">What are they into? <small>Pick one or more, or skip.</small></h2><div class="opts opts--theme">{themes}</div>
  <div class="qnav"><button type="button" class="btn btn--ghost" data-back>← Back</button><button type="button" class="btn btn--primary" data-next>Next</button></div></div>
 <div class="qstep" data-step="3" hidden><h2 class="qtitle">What's your budget?</h2><div class="opts opts--budget">{budgets}</div>
  <div class="qnav"><button type="button" class="btn btn--ghost" data-back>← Back</button></div></div>
 <div class="qstep" data-step="4" hidden>
  <div class="results-head"><h2 class="qtitle" data-rtitle>Your gift ideas</h2><button type="button" class="btn btn--ghost" data-restart>Start over</button></div>
  <p class="muted" data-rnote></p>
  <div class="grid" data-results></div>
  <p class="disclose">We may earn a commission from Amazon links, at no extra cost to you.</p>
  {note()}
 </div>
</section>
<script>window.__GIFTS={json.dumps(data, ensure_ascii=False, separators=(",", ":"))};</script>
<script src="/assets/js/finder.js" defer></script>"""
    page("/gift-finder/", "Gift Finder: Find the Perfect Gift for Any Kid in 30 Seconds | GiftScope",
         "Answer 3 quick questions (age, interests, budget) and get a short list of top-rated gift ideas from Amazon for babies, kids and teens.",
         body, active="/gift-finder/", jsonld=[cld])



# ---------- guides ----------
def guide_items(g):
    r = g["rules"]
    out = []
    for p in P:
        if "age" in r and not (p["age_min"] <= r["age"] <= p["age_max"]):
            continue
        if "themes" in r and p["theme"] not in r["themes"]:
            continue
        if p["theme"] in r.get("exclude_themes", []) and p["asin"] not in r.get("include", []):
            continue
        if not (r.get("min_price", 0) <= p["price"] <= r.get("max_price", 1e9)):
            continue
        if p["asin"] in r.get("exclude", []):
            continue
        out.append(p)
    inc = [next(p for p in P if p["asin"] == a) for a in r.get("include", [])]
    rest = [p for p in ranked(out) if p not in inc]
    return ranked(inc + rest[: r.get("limit", 15) - len(inc)])


def guide_tiles():
    out = []
    for g in GUIDES:
        items = guide_items(g)
        thumbs = "".join(f'<img src="{img(p["image"], 200)}" alt="" loading="lazy" width="100" height="100">' for p in items[:3])
        out.append(f'<a class="gtile" href="/guides/{g["slug"]}/"><span class="gtile__imgs">{thumbs}</span><span class="gtile__body"><b>{g["emoji"]} {E(g["title"])}</b><span>{E(g["pin"])}</span><small>{len(items)} picks · from {money(min(p["price"] for p in items))}</small></span></a>')
    return '<div class="gtiles">' + "".join(out) + "</div>"


def quick_picks(items):
    best = items[0]
    rest = [p for p in items if p is not best]
    budget = next((p for p in sorted(rest, key=lambda p: -p["score"]) if p["price"] <= 25), None)
    splurge = max(rest, key=lambda p: (p["price"] >= 50, p["score"] if p["price"] >= 50 else -p["price"]), default=None)
    rows = [("Best overall", best), ("Best under $25", budget)]
    if splurge and splurge["price"] > best["price"] and splurge is not budget:
        rows.append(("Worth the splurge", splurge))
    li = "".join(f'<li><span class="qp__lbl">{lbl}</span><a href="#pick-{p["asin"]}">{E(p["name"])}</a><span class="qp__price">{money(p["price"])}</span></li>' for lbl, p in rows if p)
    return f'<aside class="qp"><h2>Quick picks</h2><ol>{li}</ol></aside>'


def pick(p, i):
    th = THEME[p["theme"]]
    return f"""<article class="pick" id="pick-{p['asin']}">
 <a class="pick__media" href="{E(p['url'])}" target="_blank" rel="sponsored nofollow noopener" tabindex="-1" aria-hidden="true"><span class="card__rank">#{i}</span><img src="{img(p['image'])}" alt="" loading="lazy" width="500" height="500"></a>
 <div class="pick__body">
  <p class="card__meta"><span class="chip-age">Ages {age_label(p)}</span><span>{th['emoji']} {E(th['label'])}</span>{'<span class="card__pick card__pick--inline">Top pick</span>' if p['top'] else ''}</p>
  <h3 class="pick__title"><a href="{E(p['url'])}" target="_blank" rel="sponsored nofollow noopener">{i}. {E(p['name'])}</a></h3>
  <p>{E(p['blurb'])}</p>
  <p class="card__rating"><span class="stars" style="--r:{p['rating']}" aria-hidden="true"></span><span>{p['rating']:.1f}</span><span class="muted">({reviews_txt(p['reviews'])} ratings on Amazon)</span></p>
  <div class="card__buy"><span class="price">{money(p['price'])}<sup>*</sup></span><a class="btn btn--amz" href="{E(p['url'])}" target="_blank" rel="sponsored nofollow noopener">See on Amazon</a></div>
 </div>
</article>"""


def build_guides():
    for g in GUIDES:
        items = guide_items(g)
        if len(items) < 6:
            raise SystemExit(f"guide {g['slug']} has only {len(items)} items")
        path = f"/guides/{g['slug']}/"
        cr, cld = crumbs([("/", "Home"), ("/guides/", "Gift Guides"), (None, g["title"])])
        tips = "".join(f"<li><b>{E(t)}:</b> {E(d)}</li>" for t, d in g["tips"])
        faq = "".join(f"<details><summary>{E(q)}</summary><p>{E(a)}</p></details>" for q, a in g["faq"])
        others = [o for o in GUIDES if o is not g]
        body = f"""<section class="phead"><div class="wrap wrap--narrow">{cr}
 <h1><span class="phead__emoji" aria-hidden="true">{g['emoji']}</span>{E(g['title'])} ({CHECKED:%Y})</h1>
 {''.join(f'<p class="lead">{E(x)}</p>' for x in g['intro'])}
 <p class="phead__facts"><span>{len(items)} picks</span><span>{money(min(p['price'] for p in items))} – {money(max(p['price'] for p in items))}</span><span>Updated {CHECKED_TXT}</span></p>
 <p class="disclose">We may earn a commission from Amazon links, at no extra cost to you.</p>
</div></section>
<section class="wrap wrap--narrow guide">
 {quick_picks(items)}
 <h2 class="h2">How to choose</h2>
 <ul class="tips">{tips}</ul>
 <h2 class="h2">Our picks</h2>
 <div class="picks">{''.join(pick(p, i + 1) for i, p in enumerate(items))}</div>
 {note()}
 <div class="cta-box"><b>Still not sure?</b><span>Answer 3 quick questions and get gifts matched to their age, interests and your budget.</span><a class="btn btn--primary" href="/gift-finder/">Try the Gift Finder</a></div>
 <h2 class="h2">FAQ</h2>
 <div class="faq">{faq}</div>
</section>
{related_block("More gift guides", '<div class="pills">' + ''.join(f'<a class="pill pill--sm" href="/guides/{o["slug"]}/"><b>{o["emoji"]} {E(o["title"])}</b></a>' for o in others) + '</div>')}"""
        faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in g["faq"]]}
        art_ld = {"@context": "https://schema.org", "@type": "Article", "headline": g["title"], "dateModified": DB["checked"],
                  "image": img(items[0]["image"], 1000), "publisher": {"@type": "Organization", "name": "GiftScope"}}
        page(path, f"{g['title']} ({CHECKED:%Y}): {len(items)} Top-Rated Ideas | GiftScope",
             f"{g['intro'][0][:140].rsplit(' ', 1)[0]}… {len(items)} picks from {money(min(p['price'] for p in items))}.",
             body, active="/guides/", jsonld=[art_ld, item_list(g["title"], items), faq_ld, cld], og=img(items[0]["image"], 1000))
    cr, cld = crumbs([("/", "Home"), (None, "Gift Guides")])
    body = f'<section class="phead"><div class="wrap">{cr}<h1>Gift guides</h1><p class="lead">Short, curated lists for the most common gift questions: by age, by budget and by what they love.</p></div></section><section class="band"><div class="wrap">{guide_tiles()}</div></section>'
    page("/guides/", "Gift Guides for Kids and Teens | GiftScope", "Curated gift guides for babies, kids, tweens and teens: by age, budget and interest, with top-rated picks from Amazon.", body, active="/guides/", jsonld=[cld])


def build_static():
    pages = {
        "/about/": ("About GiftScope", f"""<p>GiftScope helps parents, grandparents, aunts, uncles and friends find a great gift for a child fast, without scrolling through thousands of listings.</p>
<p>We build each list from Amazon's toy best sellers and the themes kids ask for most (superheroes, dinosaurs, LEGO, STEM, dolls and more). We keep only products with strong ratings from many buyers and drop knock-offs, resale bundles and listings with too few reviews. Then we sort everything by age, interest and budget.</p>
<p>Prices and ratings were last checked on {CHECKED_TXT}. We refresh them regularly through the holiday season, especially before Black Friday and Cyber Monday.</p>
<p>GiftScope is part of the SpecVersus family of buying guides, alongside <a href="https://scooters.specversus.com/">ScooterScope</a>, <a href="https://robotvacuums.specversus.com/">VacScope</a> and <a href="https://powerstations.specversus.com/">PowerScope</a>.</p>
<p>Questions or corrections: <a href="mailto:hello@specversus.com">hello@specversus.com</a></p>"""),
        "/disclosure/": ("Affiliate Disclosure", """<p><strong>GiftScope is a participant in the Amazon Services LLC Associates Program</strong>, an affiliate advertising program designed to provide a means for sites to earn advertising fees by advertising and linking to Amazon.com.</p>
<p>As an Amazon Associate I earn from qualifying purchases. When you click a product link and buy on Amazon, we may earn a small commission. It costs you nothing extra and never changes the price you pay.</p>
<p>Commissions do not decide which products we include. We choose gifts based on what kids like, ratings from real buyers and value for money.</p>
<p>Prices, ratings and availability shown on GiftScope were accurate on the date stated and may change. The price and availability displayed on Amazon at the time of purchase apply.</p>"""),
        "/privacy/": ("Privacy Policy", """<p>GiftScope does not ask for, collect or store personal information. There are no accounts, forms or newsletters.</p>
<p><strong>Gift Finder:</strong> your answers stay in your browser and are not sent to us.</p>
<p><strong>Amazon:</strong> when you click a product link you go to Amazon.com, which may set cookies to track the referral for the Associates program. Amazon's privacy notice applies on their site.</p>
<p><strong>Hosting:</strong> our host (Netlify) may keep standard server logs, such as IP address and browser type, for security and performance.</p>
<p><strong>Children:</strong> GiftScope is written for adults shopping for children. It is not directed to children under 13, and we do not knowingly collect information from children.</p>
<p>Contact: <a href="mailto:hello@specversus.com">hello@specversus.com</a></p>"""),
    }
    for path, (h1, txt) in pages.items():
        cr, cld = crumbs([("/", "Home"), (None, h1)])
        body = f'<section class="phead"><div class="wrap">{cr}<h1>{h1}</h1></div></section><section class="wrap prose">{txt}</section>'
        page(path, f"{h1} | GiftScope", f"{h1} for GiftScope, the holiday gift guide for kids and teens.", body, jsonld=[cld])
    body = f'<section class="phead"><div class="wrap"><h1>Page not found</h1><p class="lead">That page doesn\'t exist, but the perfect gift might.</p><div class="hero__cta"><a class="btn btn--primary" href="/gift-finder/">Gift Finder</a><a class="btn btn--ghost" href="/">Home</a></div></div></section><section class="band"><div class="wrap">{tiles_age()}</div></section>'
    page("/404.html", "Page not found | GiftScope", "Page not found.", body)


def build_meta():
    today = dt.date.today().isoformat()
    urls = "".join(f"<url><loc>{DOMAIN}{u}</loc><lastmod>{today}</lastmod></url>" for u in PAGES)
    (DIST / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n")


def validate():
    import re
    bad = []
    for f in DIST.rglob("*.html"):
        t = f.read_text()
        for u in re.findall(r'https://www\.amazon\.com/[^"\'\s<]+', t):
            if f"tag={TAG}" not in u:
                bad.append((f, u))
        for a in re.findall(r'<a [^>]*href="https://www\.amazon\.com[^>]*>', t):
            if 'rel="sponsored nofollow noopener"' not in a:
                bad.append((f, "missing sponsored rel: " + a[:80]))
    for p in P:
        assert p["url"] == f"https://www.amazon.com/dp/{p['asin']}?tag={TAG}", p
    if bad:
        raise SystemExit(f"link check failed: {bad[:5]}")
    assert len(PAGES) == len(set(PAGES)), "duplicate pages"


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(SRC, DIST)
    build_home()
    build_hubs()
    build_listings()
    build_finder()
    build_guides()
    build_static()
    build_meta()
    validate()
    print(f"built {len(PAGES)} pages, {len(P)} products -> {DIST}")


if __name__ == "__main__":
    main()
