"""Build the whole site into docs/ from data/*.json.

  python3 scripts/build.py                     # local preview (no tracking, noindex)
  python3 scripts/build.py --base /ccs-website # GitHub Pages project preview
  python3 scripts/build.py --live              # production: tracking on, indexable, base ""

Edit content in data/site.json (business info, services, towns, reviews, FAQ),
data/projects.json and data/articles.json. Layout lives in this file + css/styles.css.
"""
import json, re, html, shutil, sys, pathlib
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs"
args = sys.argv[1:]
LIVE = "--live" in args
BASE = args[args.index("--base") + 1].rstrip("/") if "--base" in args else ""
V = "15"  # cache-bust css/js; bump on every change

S = json.loads((ROOT / "data" / "site.json").read_text())
PROJECTS = json.loads((ROOT / "data" / "projects.json").read_text())
ARTICLES = json.loads((ROOT / "data" / "articles.json").read_text())
OLD = json.loads((ROOT / "data" / "old_content.json").read_text())
IMAGES = json.loads((ROOT / "data" / "images.json").read_text())
B = S["business"]
DOMAIN = B["domain"]
SERVICES = {s["key"]: s for s in S["services"]}
TOWNS = {t["key"]: t for t in S["towns"]}
FAQ = S["faq"]
TODAY = date.today().isoformat()
for _a in ARTICLES: _a["title"] = _a["title"].split(" | ")[0].strip()
FEATURED = ["heat-pump-installation-wimberley-tx", "hvac-replacement-austin-tx", "carrier-ductless-installation-in-austin-tx",
            "carrier-HVAC-installation-kyle-tx", "heat-pump-upgrade-austin-tx", "5-ton-gas-system-changeout-ausin-tx"]
SHOWCASE = sorted(PROJECTS, key=lambda p: FEATURED.index(p["slug"]) if p["slug"] in FEATURED else 99)
PAGES = []  # (path, priority) for sitemap

esc = html.escape

def url(path=""):
    return f"{BASE}/{path}"

def abs_url(path=""):
    return f"{DOMAIN}/{path}"

def out_file(path):
    if path == "": return OUT / "index.html"
    if path.endswith("/"): return OUT / path / "index.html"
    return OUT / (path + ".html")

def rebase(h):
    """Point root-relative links in imported HTML at BASE, open external links in a new tab."""
    h = h.replace('href="/air-quality/"', 'href="/air-quality"')
    h = re.sub(r'<a href="/(?:fbm|uplift)-data/[^"]*">\s*(<img[^>]*>)?\s*</a>', "", h)
    h = re.sub(r'<a href="/cdn-cgi/l/email-protection[^"]*">.*?</a>', "us", h, flags=re.S)
    h = re.sub(r"<(/?)h1>", r"<\1h2>", h)
    h = re.sub(r'href="/(?!/)', f'href="{BASE}/', h)
    h = re.sub(r'href="(https?://(?!www\.ccsolutionsatx\.com)[^"]+)"', r'href="\1" target="_blank" rel="noopener"', h)
    h = h.replace('href="https://www.ccsolutionsatx.com/', f'href="{BASE}/')
    return h

# ---------- icons ----------
ICONS = {
    "phone": '<path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z" fill="currentColor"/>',
    "calendar": '<rect x="3.5" y="5" width="17" height="15.5" rx="2.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3.5 10h17M8 3v4M16 3v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    "star": '<path d="M12 2.8l2.8 5.9 6.4.8-4.7 4.4 1.2 6.4L12 17.2l-5.7 3.1 1.2-6.4-4.7-4.4 6.4-.8z" fill="currentColor"/>',
    "wrench": '<path d="M14.7 6.3a4.5 4.5 0 0 0-5.9 5.6L3.5 17.2a2 2 0 1 0 2.8 2.8l5.3-5.3a4.5 4.5 0 0 0 5.6-5.9l-2.7 2.7-2.4-.4-.4-2.4z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>',
    "unit": '<rect x="3" y="4" width="18" height="16" rx="2.5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 7.5v9M7.5 12h9" stroke="currentColor" stroke-width="1.5"/>',
    "gauge": '<path d="M4 16a8 8 0 1 1 16 0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M12 16l4-5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="12" cy="16" r="1.6" fill="currentColor"/>',
    "flame": '<path d="M12 3c1 3.5 5 5.5 5 10a5 5 0 0 1-10 0c0-2.2 1.2-3.6 2.3-4.6.2 1.6 1 2.6 2 3.1C11 9.5 11 6 12 3z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>',
    "snow": '<path d="M12 2.5v19M4 7l16 10M4 17L20 7M9.5 4.5L12 7l2.5-2.5M9.5 19.5L12 17l2.5 2.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
    "leaf": '<path d="M5 19c0-8 5-13 15-14-1 10-6 15-14 15M5 19l7-7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    "pin": '<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="9.5" r="2.5" fill="currentColor"/>',
    "shield": '<path d="M12 3l7.5 3v5.5c0 4.6-3.2 8.3-7.5 9.5-4.3-1.2-7.5-4.9-7.5-9.5V6z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M8.5 12l2.5 2.5 4.5-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    "clock": '<circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 7.5V12l3 2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    "home": '<path d="M4 11l8-6.5 8 6.5V20a1 1 0 0 1-1 1h-4.5v-6h-5v6H5a1 1 0 0 1-1-1z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>',
    "card": '<rect x="3" y="5.5" width="18" height="13" rx="2.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3 10h18M7 15h4" stroke="currentColor" stroke-width="2"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    "close": '<path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    "chev": '<path d="M7 10l5 5 5-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    "fb": '<path d="M14 8.5V6.8c0-.8.5-1.3 1.4-1.3H17V2.6c-.3 0-1.3-.1-2.5-.1-2.5 0-4.1 1.5-4.1 4.2v1.8H7.7v3.2h2.7V21H14v-9.3h2.7l.4-3.2z" fill="currentColor"/>',
    "ig": '<rect x="3.5" y="3.5" width="17" height="17" rx="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.2" cy="6.8" r="1.2" fill="currentColor"/>',
}

def icon(name, cls="i"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{ICONS[name]}</svg>'

LOGO_MARK = ('<svg class="logo-mark" viewBox="0 0 96 72" aria-hidden="true" focusable="false">'
             '<path d="M52.4 17.6A26 26 0 1 0 52.4 54.4" fill="none" stroke="#FE0700" stroke-width="11" stroke-linecap="butt"/>'
             '<path d="M80.4 17.6A26 26 0 1 0 80.4 54.4" fill="none" stroke="#0C48F6" stroke-width="11" stroke-linecap="butt"/></svg>')

def logo(cls=""):
    return (f'<a class="logo {cls}" href="{url()}" aria-label="{esc(B["name"])} home">{LOGO_MARK}'
            f'<span class="logo-word"><span>Climate Control</span><span>Solutions</span></span></a>')

# ---------- images ----------
ALL_IMAGES = dict(IMAGES, **{im["name"]: im for p in PROJECTS for im in p["images"]})

def img(meta, alt, sizes="100vw", cls="", eager=False, ratio=None):
    if isinstance(meta, str): meta = ALL_IMAGES[meta]
    name, widths = meta["name"], meta["widths"]
    srcset = ", ".join(f"{url(f'assets/img/{name}-{w}.webp')} {w}w" for w in widths)
    mid = widths[min(1, len(widths) - 1)]
    w, h = meta["w"], meta["h"]
    load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    style = f' style="aspect-ratio:{ratio}"' if ratio else ""
    return (f'<img src="{url(f"assets/img/{name}-{mid}.webp")}" srcset="{srcset}" sizes="{sizes}" '
            f'width="{w}" height="{h}" alt="{esc(alt)}" class="{cls}" {load}{style}>')

def img_url(meta, w=None):
    if isinstance(meta, str): meta = ALL_IMAGES[meta]
    w = w or meta["widths"][-1]
    return abs_url(f"assets/img/{meta['name']}-{w}.webp")

# ---------- schema ----------
def business_node(full=True):
    node = {"@type": "HVACBusiness", "@id": f"{DOMAIN}/#business", "name": B["name"], "url": f"{DOMAIN}/"}
    if not full: return node
    node.update({
        "telephone": B["phone_tel"],
        "image": img_url("site/van"),
        "logo": abs_url("assets/logo-512.png"),
        "description": "Family-owned heating and air conditioning company in Kyle, TX providing AC and heating repair, replacement, maintenance and indoor air quality service, with 24/7 emergency service.",
        "address": {"@type": "PostalAddress", "streetAddress": B["street"], "addressLocality": B["city"], "addressRegion": B["region"], "postalCode": B["zip"], "addressCountry": "US"},
        "areaServed": [{"@type": "City", "name": f"{t['name']}, TX"} for t in S["towns"]],
        "hasMap": B["google_reviews_url"],
        "sameAs": [B["facebook"], B["instagram"], B["google_reviews_url"]],
        "knowsAbout": ["Air conditioning repair", "AC replacement", "Heat pumps", "Furnace repair", "HVAC maintenance", "Indoor air quality", "Ductless mini-splits"],
        "slogan": "24/7 emergency heating and air conditioning service",
        "makesOffer": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": s["name"], "url": abs_url(s["path"])}} for s in S["services"]]
                      + [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Gold Service Plan (HVAC maintenance membership)", "url": abs_url("gold-service-plan")}}],
        "paymentAccepted": "Financing available",
        "identifier": {"@type": "PropertyValue", "name": "Texas ACR contractor license", "value": B["license"]},
    })
    return node

def breadcrumb_schema(crumbs):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": abs_url(p)} for i, (n, p) in enumerate(crumbs)]}

def faq_schema(items):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in items]}

def ld(nodes):
    return f'<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@graph": nodes}, ensure_ascii=False)}</script>'

# ---------- page chrome ----------
def tracking_head():
    if not LIVE: return ""
    t = S["tracking"]
    return f"""<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);}})(window,document,'script','dataLayer','{t["gtm"]}');</script>
<script>!function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');fbq('init','{t["meta_pixel"]}');fbq('track','PageView');</script>
"""

def tracking_body():
    if not LIVE: return ""
    return f'<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={S["tracking"]["gtm"]}" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>\n'

def head(path, title, desc, schema, og_image=None, og_alt=None):
    og_image = og_image or abs_url("assets/og-image.jpg")
    og_alt = og_alt or f"{B['name']}: heating and air conditioning in Kyle, Buda and South Austin, TX"
    robots = '<meta name="robots" content="index, follow, max-image-preview:large">' if LIVE else '<meta name="robots" content="noindex, nofollow">'
    return f"""<!doctype html>
<html lang="en-US">
<head>
{tracking_head()}<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{robots}
<link rel="canonical" href="{abs_url(path)}">
<link rel="preload" href="{url('assets/fonts/archivo-latin-800-normal.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{url('assets/fonts/inter-latin-400-normal.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{url('css/styles.css')}?v={V}">
<meta name="theme-color" content="#0B1A33">
<link rel="icon" href="{url('assets/favicon.svg')}" type="image/svg+xml">
<link rel="icon" href="{url('assets/favicon-64.png')}" sizes="64x64" type="image/png">
<link rel="apple-touch-icon" href="{url('assets/apple-touch-icon.png')}">
<link rel="manifest" href="{url('site.webmanifest')}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(B['name'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{abs_url(path)}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(og_alt)}">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{og_image}">
{ld(schema)}
</head>
"""

NAV = [
    ("Cooling", "air-conditioning/", [("ac-repair", None), ("ac-replacement", None), ("ac-maintenance", None), (None, ("All cooling services", "air-conditioning/"))]),
    ("Heating", "heating/", [("heating-repair", None), ("heating-replacement", None), ("heating-maintenance", None), (None, ("All heating services", "heating/"))]),
    ("Air Quality", "air-quality", None),
    ("Gold Plan", "gold-service-plan", None),
    ("Service Area", "near-me/", None),
    ("Reviews", "reviews", None),
    ("About", "about-us", [(None, ("About us", "about-us")), (None, ("Projects", "projects/")), (None, ("FAQ", "faq")), (None, ("HVAC tips", "air-conditioning-tips/")), (None, ("Financing", B["financing_url"])), (None, ("Contact", "contact-us"))]),
]

def nav_link(label, target, current):
    ext = target.startswith("http")
    href = target if ext else url(target)
    cur = ' aria-current="page"' if (not ext and target == current) else ""
    extra = ' target="_blank" rel="noopener"' if ext else ""
    return f'<a href="{href}"{cur}{extra}>{esc(label)}</a>'

def header(current):
    items = []
    for label, target, sub in NAV:
        if not sub:
            items.append(f'<li>{nav_link(label, target, current)}</li>')
            continue
        links = []
        for key, alt in sub:
            if key: links.append(f'<li>{nav_link(SERVICES[key]["name"], SERVICES[key]["path"], current)}</li>')
            else: links.append(f'<li>{nav_link(alt[0], alt[1], current)}</li>')
        active = " is-active" if current.startswith(target.rstrip("/")) and target else ""
        items.append(f'<li class="has-sub{active}"><button class="nav-top" aria-expanded="false">{esc(label)}{icon("chev", "i chev")}</button>'
                     f'<ul class="sub">{"".join(links)}</ul></li>')
    return f"""<a class="skip" href="#main">Skip to content</a>
<a class="topbar" href="tel:{B['phone_tel']}" data-call><span class="wrap topbar-in"><span class="tb-dot" aria-hidden="true"></span><strong>24/7 Emergency<span class="lbl-lg"> Service</span></strong><span class="tb-sep" aria-hidden="true">·</span><span class="tb-call">{icon('phone')} <span class="lbl-lg">Call&nbsp;</span>{B['phone']}</span></span></a>
<header class="site-header"><div class="wrap header-in">
{logo()}
<nav class="nav" id="nav" aria-label="Main">
<ul class="nav-list">{''.join(items)}</ul>
<div class="nav-cta">
<a class="btn btn-red btn-block" href="tel:{B['phone_tel']}" data-call>{icon('phone')} Call {B['phone']}</a>
<a class="btn btn-blue btn-block" href="{B['booking_url']}" target="_blank" rel="noopener" data-book>{icon('calendar')} Book online</a>
</div>
</nav>
<div class="header-actions">
<a class="h-phone" href="tel:{B['phone_tel']}" data-call>{icon('phone')}<span><small>Call 24/7</small>{B['phone']}</span></a>
<a class="btn btn-blue btn-sm" href="{B['booking_url']}" target="_blank" rel="noopener" data-book><span class="lbl-lg">Book online</span><span class="lbl-sm">Book</span></a>
<button class="menu-btn" aria-controls="nav" aria-expanded="false" aria-label="Open menu">{icon('menu', 'i i-menu')}{icon('close', 'i i-close')}</button>
</div>
</div></header>
"""

def footer():
    svc = "".join(f'<li><a href="{url(s["path"])}">{esc(s["name"])}</a></li>' for s in S["services"]) + f'<li><a href="{url("gold-service-plan")}">Gold Service Plan</a></li>'
    towns = "".join(f'<li><a href="{url(t["path"])}">{esc(t["name"])}, TX</a></li>' for t in S["towns"])
    return f"""<footer class="site-footer">
<div class="wrap footer-grid">
<div class="f-brand">
{logo('logo-light')}
<p>Family-owned heating &amp; air conditioning serving Kyle, Buda, San Marcos, Wimberley, Dripping Springs and South Austin.</p>
<address>{B['street']}<br>{B['city']}, {B['region']} {B['zip']}<br><a href="tel:{B['phone_tel']}" data-call>{B['phone']}</a></address>
<p class="f-lic">Texas ACR License {B['license']}<br>24/7 emergency service</p>
<div class="f-social"><a href="{B['facebook']}" target="_blank" rel="noopener" aria-label="Facebook">{icon('fb')}</a><a href="{B['instagram']}" target="_blank" rel="noopener" aria-label="Instagram">{icon('ig')}</a><a class="f-google" href="{B['google_reviews_url']}" target="_blank" rel="noopener"><span class="stars" aria-hidden="true">★★★★★</span> {B['rating']} on Google</a></div>
</div>
<div><h2 class="f-h">Services</h2><ul>{svc}</ul></div>
<div><h2 class="f-h">Service area</h2><ul class="f-towns">{towns}</ul></div>
<div><h2 class="f-h">Company</h2><ul>
<li><a href="{url('about-us')}">About us</a></li><li><a href="{url('reviews')}">Reviews</a></li><li><a href="{url('projects/')}">Projects</a></li>
<li><a href="{url('air-conditioning-tips/')}">HVAC tips</a></li><li><a href="{url('faq')}">FAQ</a></li>
<li><a href="{B['financing_url']}" target="_blank" rel="noopener">Financing</a></li><li><a href="{url('contact-us')}">Contact</a></li>
</ul></div>
</div>
<div class="wrap footer-base">
<span>© {date.today().year} {B['name']}. All rights reserved.</span>
<span><a href="{url('privacy')}">Privacy</a> · <a href="{url('terms')}">Terms</a> · <a href="{url('sitemap')}">Sitemap</a></span>
</div>
</footer>
<div class="mobile-bar"><a class="btn btn-red" href="tel:{B['phone_tel']}" data-call>{icon('phone')} Call now</a><a class="btn btn-blue" href="{B['booking_url']}" target="_blank" rel="noopener" data-book>{icon('calendar')} Book online</a></div>
<script src="{url('js/main.js')}?v={V}" defer></script>
"""

def page(path, title, desc, main, schema, current=None, og_image=None, og_alt=None, priority="0.6", sitemap=True, body_cls=""):
    doc = head(path, title, desc, schema, og_image, og_alt) + f'<body class="{body_cls}">\n{tracking_body()}' + header(current if current is not None else path) + f'<main id="main">\n{main}\n</main>\n' + footer() + "</body>\n</html>\n"
    f = out_file(path); f.parent.mkdir(parents=True, exist_ok=True); f.write_text(doc)
    if sitemap: PAGES.append((path, priority))

# ---------- sections ----------
def crumbs_html(crumbs):
    parts = []
    for i, (n, p) in enumerate(crumbs):
        if i == len(crumbs) - 1: parts.append(f'<li aria-current="page">{esc(n)}</li>')
        else: parts.append(f'<li><a href="{url(p)}">{esc(n)}</a></li>')
    return f'<nav class="crumbs" aria-label="Breadcrumb"><ol>{"".join(parts)}</ol></nav>'

def stars():
    return '<span class="stars" aria-hidden="true">★★★★★</span>'

def rating_badge(cls=""):
    return (f'<a class="rating-badge {cls}" href="{B["google_reviews_url"]}" target="_blank" rel="noopener">'
            f'<strong>{B["rating"]}</strong><span>{stars()}<small>{B["review_count"]} Google reviews</small></span></a>')

def cta_buttons(cls="", book_label="Book online"):
    return (f'<div class="btn-row {cls}"><a class="btn btn-red btn-lg" href="tel:{B["phone_tel"]}" data-call>{icon("phone")} Call {B["phone"]}</a>'
            f'<a class="btn btn-blue btn-lg" href="{B["booking_url"]}" target="_blank" rel="noopener" data-book>{icon("calendar")} {book_label}</a></div>')

def page_hero(crumbs, h1, lede, image=None, image_alt="", eyebrow=None):
    pic = f'<div class="ph-media">{img(image, image_alt, "(max-width:900px) 100vw, 40vw", "ph-img", eager=True)}</div>' if image else ""
    eb = f'<p class="eyebrow on-dark">{esc(eyebrow)}</p>' if eyebrow else ""
    return f"""<section class="page-hero{' has-media' if image else ''}"><div class="wrap ph-in">
<div class="ph-text">{crumbs_html(crumbs)}{eb}<h1>{esc(h1)}</h1><p class="lede">{lede}</p>{cta_buttons()}
<div class="ph-trust">{rating_badge('on-dark')}<span class="ph-chip">{icon('clock')} 24/7 emergency service</span></div></div>
{pic}</div></section>"""

def section_head(eyebrow, h2, sub="", center=False, dark=False):
    return (f'<div class="sec-head{" center" if center else ""}"><p class="eyebrow{" on-dark" if dark else ""}">{esc(eyebrow)}</p>'
            f'<h2>{h2}</h2>{f"<p class=sec-sub>{sub}</p>" if sub else ""}</div>')

def reviews_section(n=6, alt=False, eyebrow="Reviews", h2=None):
    h2 = h2 or f"{B['review_count']} Google reviews, {B['rating']} stars"
    cards = "".join(f"""<figure class="review">{stars()}<blockquote>“{esc(r['text'])}”</blockquote>
<figcaption><span class="r-name">{esc(r['name'])}</span><span class="r-tag">{esc(r['tag'])} · Google review</span></figcaption></figure>"""
                    for r in S["reviews"][:n])
    return f"""<section class="section{' section-alt' if alt else ''}" id="reviews"><div class="wrap">
<div class="sec-head-row">{section_head(eyebrow, h2, "What Kyle, Buda and Austin homeowners say. The word that comes up most: honest.")}
<a class="btn btn-ghost" href="{B['google_reviews_url']}" target="_blank" rel="noopener">Read all reviews on Google {icon('arrow')}</a></div>
<div class="reviews scroller" data-swipe>{cards}</div><p class="swipe-hint" aria-hidden="true">Swipe →</p>
</div></section>"""

def service_cards(keys=None, h_level=3):
    keys = keys or [s["key"] for s in S["services"]]
    out = []
    for k in keys:
        s = SERVICES[k]
        out.append(f"""<a class="svc-card svc-{s['group']}" href="{url(s['path'])}">
<span class="svc-ico">{icon(s['icon'])}</span><h{h_level}>{esc(s['name'])}</h{h_level}><p>{esc(s['card'])}</p><span class="more">Learn more {icon('arrow')}</span></a>""")
    return "".join(out)

def project_cards(projects, n=6):
    out = []
    for p in projects[:n]:
        if not p["images"]: continue
        town = TOWNS.get(p["town"], {}).get("name", "")
        out.append(f"""<a class="proj-card" href="{url('projects/' + p['slug'])}">
<div class="proj-img">{img(p['images'][0], p['title'], "(max-width:700px) 80vw, (max-width:1100px) 45vw, 360px")}</div>
<div class="proj-body">{f'<span class="proj-town">{icon("pin")} {esc(town)}, TX</span>' if town else ''}<h3>{esc(p['title'])}</h3>
{f'<span class="proj-brand">{esc(p["products"])}</span>' if p['products'] else ''}</div></a>""")
    return "".join(out)

def projects_section(projects, h2="Recent installs & repairs", sub="Real jobs from our crew across Hays County and Austin.", alt=False):
    if not [p for p in projects if p["images"]]: return ""
    return f"""<section class="section{' section-alt' if alt else ''}"><div class="wrap">
<div class="sec-head-row">{section_head("Our work", h2, sub)}<a class="btn btn-ghost" href="{url('projects/')}">All projects {icon('arrow')}</a></div>
<div class="proj-grid scroller" data-swipe>{project_cards(projects)}</div><p class="swipe-hint" aria-hidden="true">Swipe →</p>
</div></section>"""

def faq_section(items, h2="Frequently asked questions", alt=False, link_all=True):
    qa = "".join(f'<details class="faq-item"><summary><span>{esc(f["q"])}</span>{icon("chev", "i chev")}</summary><div class="faq-a"><p>{esc(f["a"])}</p></div></details>' for f in items)
    more = f'<p class="faq-more"><a href="{url("faq")}">See all FAQs {icon("arrow")}</a></p>' if link_all else ""
    return f"""<section class="section{' section-alt' if alt else ''}" id="faq"><div class="wrap faq-wrap">
{section_head("FAQ", h2)}<div class="faq-list">{qa}{more}</div></div></section>"""

def towns_section(alt=False, exclude=None):
    links = "".join(f'<li><a href="{url(t["path"])}">{icon("pin")}<span>{esc(t["name"])}</span></a></li>' for t in S["towns"] if t["key"] != exclude)
    return f"""<section class="section{' section-alt' if alt else ''}"><div class="wrap area">
<div>{section_head("Service area", "Based in Kyle. Serving Hays County &amp; South Austin.", f"Our shop is at {B['street']} in Kyle, so we're close to every town below.")}
<a class="btn btn-ghost" href="{url('near-me/')}">View service area {icon('arrow')}</a></div>
<ul class="town-list">{links}</ul></div></section>"""

def gold_band():
    return f"""<section class="section section-dark gold"><div class="wrap gold-in">
<div>{section_head("Gold Service Plan", "Two tune-ups a year. Priority service. 10% off repairs.", "Our maintenance plan keeps your system ready for Texas summers and cold snaps, and moves you to the front of the line when the weather turns.", dark=True)}
<div class="btn-row"><a class="btn btn-gold btn-lg" href="{url('gold-service-plan')}">See the Gold Plan {icon('arrow')}</a></div></div>
<ul class="gold-list">
<li>{icon('snow')}<span><strong>Spring AC tune-up</strong> before the heat arrives</span></li>
<li>{icon('flame')}<span><strong>Fall heating check</strong> with a CO safety test</span></li>
<li>{icon('clock')}<span><strong>Priority scheduling</strong> during heat waves and cold fronts</span></li>
<li>{icon('check')}<span><strong>10% off all repairs</strong>, applied right on the ticket</span></li>
</ul></div></section>"""

def financing_strip():
    return f"""<div class="fin-strip">{icon('card')}<p><strong>Financing available.</strong> Spread the cost of a new system into monthly payments through FTL Finance.</p>
<a class="btn btn-ghost btn-sm" href="{B['financing_url']}" target="_blank" rel="noopener">Check financing {icon('arrow')}</a></div>"""

def cta_band(h="Need heating or AC help today?", sub="Call now for 24/7 emergency service, or book a time that works for you."):
    return f"""<section class="cta-band"><div class="wrap cta-in"><div><h2>{h}</h2><p>{sub}</p></div>{cta_buttons()}</div></section>"""

def brand_strip():
    return f"""<div class="brands"><p>We service all major brands</p><ul>{''.join(f'<li>{esc(b)}</li>' for b in B['brands'])}</ul></div>"""

def article_cards(arts, n=3):
    out = []
    for a in arts[:n]:
        pic = f'<div class="art-img">{img(a["image"], a["title"], "(max-width:700px) 86vw, 360px")}</div>' if a["image"] else f'<div class="art-img art-ph">{icon("snow")}</div>'
        out.append(f'<a class="art-card" href="{url("air-conditioning-tips/" + a["slug"])}">{pic}<div class="art-body"><h3>{esc(a["title"])}</h3><p>{esc(a["excerpt"][:150].rsplit(" ", 1)[0])}…</p><span class="more">Read article {icon("arrow")}</span></div></a>')
    return "".join(out)

# ---------- pages ----------
def build_home():
    faqs = [f for f in FAQ if f.get("home")]
    proof = ["Honest diagnosis. Repair when repair makes sense.", "On time, with updates on arrival.", "Owner-led and family-owned.", "Every major brand and model."]
    options = [("wrench", "Get a repair", "AC or heat not working right", url("air-conditioning/ac-repair"), ""),
               ("gauge", "Schedule maintenance", "Tune-ups &amp; the Gold Plan", url("air-conditioning/ac-maintenance"), ""),
               ("unit", "New system estimate", "Replace an old AC or heater", url("air-conditioning/ac-replacement"), ""),
               ("calendar", "Book online", "Pick a time that works", B["booking_url"], ' target="_blank" rel="noopener" data-book')]
    opts = "".join(f'<li><a class="opt" href="{h}"{x}><span class="opt-ico">{icon(i)}</span><span class="opt-txt"><strong>{t}</strong><small>{d}</small></span>{icon("arrow", "i opt-arr")}</a></li>' for i, t, d, h, x in options)
    main = f"""<section class="hero"><div class="wrap hero-in">
<div class="hero-text">
<h1>Heating &amp; air conditioning for Kyle, Buda &amp; South Austin</h1>
<a class="hero-rating" href="{B['google_reviews_url']}" target="_blank" rel="noopener">{stars()} <strong>{B['rating']}</strong> from {B['review_count']} Google reviews · Family-owned in Kyle</a>
<p class="hero-ask">How can we help you?</p>
<ul class="opts">{opts}</ul>
</div>
<div class="hero-media">
{img('site/van', 'Climate Control Solutions service van parked outside a home in the Kyle area', '(max-width:900px) 92vw, 44vw', 'hero-img', eager=True)}
</div>
</div></section>

<section class="emergency"><div class="wrap emergency-in">
<div><h2>Have an emergency?</h2><p>Call for immediate service, day or night.</p></div>
<a class="btn btn-red btn-xl" href="tel:{B['phone_tel']}" data-call>{icon('phone')} Call {B['phone']}</a>
</div></section>

<section class="section"><div class="wrap">
<div class="sec-head-row">{section_head("Services", "Everything your heating &amp; cooling needs", "Repairs, new systems, tune-ups and cleaner air, for every major brand and model.")}
<div class="btn-row"><a class="btn btn-ghost" href="{url('air-conditioning/')}">Cooling {icon('arrow')}</a><a class="btn btn-ghost" href="{url('heating/')}">Heating {icon('arrow')}</a></div></div>
<div class="svc-grid">{service_cards()}<a class="svc-card svc-gold" href="{url('gold-service-plan')}"><span class="svc-ico">{icon('star')}</span><h3>Gold Service Plan</h3><p>Two tune-ups a year, priority scheduling and 10% off repairs.</p><span class="more">See the plan {icon('arrow')}</span></a></div>
{brand_strip()}
</div></section>

{reviews_section(6, alt=True)}

<section class="section"><div class="wrap why">
<div class="why-media">{img('site/condenser-stone', 'New outdoor AC condenser installed beside a stone home', '(max-width:900px) 92vw, 40vw', 'why-img')}
<div class="why-card"><strong>Marcus</strong><span>Owner &amp; service technician, 10+ years in HVAC</span></div></div>
<div class="why-text">{section_head("Why Climate Control Solutions", "The HVAC company that tells you the truth.")}
<p>Our owner, Marcus, has more than a decade in the trade and still runs the business the way he'd want his own home treated. We find the real problem, explain your options in plain English and let you decide. If your system has years left in it, we'll tell you.</p>
<ul class="checks">{''.join(f'<li>{icon("check")}<span>{esc(p)}</span></li>' for p in proof)}</ul>
<a class="btn btn-ghost" href="{url('about-us')}">About us {icon('arrow')}</a>
</div></div></section>

{projects_section(SHOWCASE, alt=True)}

<section class="section"><div class="wrap">
{section_head("How it works", "Comfortable again in three steps", center=True)}
<ol class="steps">
<li><span class="step-n">1</span><h3>Call or book online</h3><p>Reach us 24/7 at {B['phone']} or pick a time online. Gold members get priority.</p></li>
<li><span class="step-n">2</span><h3>Honest diagnosis</h3><p>We test the whole system, show you what we find and give you clear options before any work starts.</p></li>
<li><span class="step-n">3</span><h3>Fixed right</h3><p>We do the work cleanly, explain what we did and make sure your home is comfortable before we leave.</p></li>
</ol>
{financing_strip()}
</div></section>

{gold_band()}
{towns_section()}
{faq_section(faqs, alt=True)}

<section class="section"><div class="wrap">
<div class="sec-head-row">{section_head("HVAC tips", "Advice for Central Texas homes")}<a class="btn btn-ghost" href="{url('air-conditioning-tips/')}">All articles {icon('arrow')}</a></div>
<div class="art-grid scroller" data-swipe>{article_cards(ARTICLES)}</div><p class="swipe-hint" aria-hidden="true">Swipe →</p>
</div></section>
{cta_band()}"""
    schema = [business_node(), {"@type": "WebSite", "@id": f"{DOMAIN}/#website", "name": B["name"], "url": f"{DOMAIN}/", "publisher": {"@id": f"{DOMAIN}/#business"}}, faq_schema(faqs)]
    page("", f"Climate Control Solutions | HVAC in Kyle & Austin, TX",
         "Family-owned heating & AC repair, replacement and maintenance in Kyle, Buda, San Marcos & South Austin. 4.9★ on Google, 24/7 emergency service.",
         main, schema, priority="1.0", body_cls="home")

def build_service(s):
    faqs = [FAQ[i] for i in s["faq"]]
    parent = {"cooling": ("Cooling", "air-conditioning/"), "heating": ("Heating", "heating/")}.get(s["group"])
    crumbs = [("Home", "")] + ([parent] if parent else []) + [(s["name"], s["path"])]
    signs = "".join(f'<li class="sign">{icon("check")}<div><h3>{esc(t)}</h3><p>{esc(d)}</p></div></li>' for t, d in s["signs"])
    body = "".join(f"<p>{esc(p)}</p>" for p in s["body"])
    related = [k for k in SERVICES if k != s["key"] and SERVICES[k]["group"] == s["group"]] or [k for k in SERVICES if k != s["key"]][:3]
    tag = {"cooling": "ac", "heating": "heat", "air": "air"}[s["group"]]
    rel_projects = [p for p in SHOWCASE if p["images"]]
    main = f"""{page_hero(crumbs, s['h1'], esc(s['lede']), s['image'], s['name'] + ' by Climate Control Solutions')}
<section class="section"><div class="wrap">{section_head(s['name'], esc(s['signs_title']))}<ul class="signs">{signs}</ul></div></section>
<section class="section section-alt"><div class="wrap prose-split">
<div>{section_head('Our approach', esc(s['body_title']))}<div class="prose">{body}</div></div>
<aside class="side-card"><h3>Talk to a real tech</h3><p>Call {B['phone']} any time. Emergency service is available 24/7.</p>{cta_buttons('stack')}
<ul class="mini-trust"><li>{icon('star')} {B['rating']}★ from {B['review_count']} Google reviews</li><li>{icon('shield')} TX License {B['license']}</li><li>{icon('home')} Family-owned in Kyle</li></ul></aside>
</div></section>
{reviews_section(3, eyebrow='Reviews', h2='Homeowners trust us with their ' + ('heating' if tag == 'heat' else 'AC' if tag == 'ac' else 'homes'))}
{projects_section(rel_projects, alt=True)}
<section class="section"><div class="wrap">{section_head('Related services', 'More ways we can help')}<div class="svc-grid svc-grid-3">{service_cards(related[:3])}</div>{financing_strip() if 'replacement' in s['key'] else ''}</div></section>
{faq_section(faqs, alt=True)}
{cta_band()}"""
    schema = [business_node(False) | {"name": B["name"]}, {"@type": "Service", "name": s["name"], "serviceType": s["name"], "url": abs_url(s["path"]),
              "description": s["description"], "provider": {"@id": f"{DOMAIN}/#business"},
              "areaServed": [{"@type": "City", "name": f"{t['name']}, TX"} for t in S["towns"]]}, breadcrumb_schema(crumbs), faq_schema(faqs)]
    page(s["path"], s["title"], s["description"], main, schema, priority="0.9", og_image=img_url(s["image"]) if False else None)

def build_hub(group, path, h1, title, desc, lede, image):
    keys = [k for k, s in SERVICES.items() if s["group"] == group]
    crumbs = [("Home", ""), (h1.split(" ")[0] if False else ("Cooling" if group == "cooling" else "Heating"), path)]
    faqs = [FAQ[i] for i in ([0, 1, 5] if group == "cooling" else [2, 5, 6])]
    main = f"""{page_hero(crumbs, h1, esc(lede), image, h1)}
<section class="section"><div class="wrap">{section_head('Services', 'Choose a service')}<div class="svc-grid svc-grid-3">{service_cards(keys, 2)}</div>{brand_strip()}</div></section>
{gold_band()}
{reviews_section(3)}
{projects_section(SHOWCASE, alt=True)}
{faq_section(faqs)}
{cta_band()}"""
    schema = [{"@type": "CollectionPage", "name": h1, "url": abs_url(path), "provider": {"@id": f"{DOMAIN}/#business"}}, breadcrumb_schema(crumbs), faq_schema(faqs)]
    page(path, title, desc, main, schema, priority="0.9")

def build_gold():
    path = "gold-service-plan"
    crumbs = [("Home", ""), ("Gold Service Plan", path)]
    faqs = [FAQ[5], FAQ[9], FAQ[2]]
    includes = [("snow", "Spring AC tune-up", "We prepare your AC for the long hot season so it cools faster and uses less energy."),
                ("flame", "Fall heating check", "Your furnace or heat pump is inspected and safety-tested before cold weather."),
                ("clock", "Priority scheduling", "Members jump to the front of the line, even during heat waves and cold fronts."),
                ("check", "10% off all repairs", "Whether we find it during a visit or you need us later, the discount goes right on the ticket."),
                ("gauge", "Better efficiency", "A clean, tuned system can help lower monthly energy costs."),
                ("shield", "Fewer surprises", "Catching worn parts early means fewer breakdowns at the worst possible time.")]
    spring = ["AC system inspection and deep cleaning", "Refrigerant check and performance test", "Thermostat calibration and control check", "Electrical, drain and condenser safety checks"]
    fall = ["Furnace or heat pump inspection", "Burner, ignition and safety controls check", "Filter replacement, if provided by the homeowner", "Airflow check and carbon monoxide safety test"]
    li = lambda xs: "".join(f'<li>{icon("check")}<span>{esc(x)}</span></li>' for x in xs)
    gold_lede = "Year-round protection for your heating and cooling: two precision tune-ups a year, priority scheduling and 10% off every repair. Enroll online with the Book online button, or call and we'll answer your questions first."
    gold_sub = "Plan pricing is per system. Call or book online and we'll walk you through it."
    main = f"""{page_hero(crumbs, 'Gold Service Plan', gold_lede, 'site/condensers', 'Two outdoor AC condensers on a gravel pad', eyebrow='HVAC maintenance plan')}
<section class="section"><div class="wrap">{section_head('Membership', 'What the Gold Plan includes', gold_sub)}
<div class="inc-grid">{''.join(f'<div class="inc">{icon(i)}<h3>{esc(t)}</h3><p>{esc(d)}</p></div>' for i, t, d in includes)}</div></div></section>
<section class="section section-alt"><div class="wrap visits">
<div class="visit visit-ac">{icon('snow', 'i big')}<h2>Spring air conditioning visit</h2><p>Before Central Texas heat sets in, we get your AC ready and watch for early signs of wear that cause midsummer breakdowns.</p><ul class="checks">{li(spring)}</ul></div>
<div class="visit visit-heat">{icon('flame', 'i big')}<h2>Fall heating visit</h2><p>When nights cool down, your furnace or heat pump needs to be safe and ready. We focus on reliability and safety.</p><ul class="checks">{li(fall)}</ul></div>
</div></section>
<section class="section"><div class="wrap prose-split">
<div>{section_head('Priority service', 'How priority service works')}<div class="prose"><p>Gold members jump to the front of the line. When you call during a busy week or after a sudden weather change, your request is flagged for the next available appointment. If you need after-hours help, your plan speeds up the next service window so we can get you comfortable sooner.</p><p>Repairs found during maintenance are explained clearly, and your 10% discount is applied right on the ticket.</p>
<p><strong>Tip:</strong> book your spring visit before late April and your fall visit before early November to beat the seasonal rush.</p></div></div>
<aside class="side-card"><h3>Join the Gold Plan</h3><p>Enroll online, or call first and we'll answer your questions before you schedule.</p>{cta_buttons('stack', 'Enroll online')}</aside>
</div></section>
{reviews_section(3, alt=True)}
{faq_section(faqs)}
{cta_band()}"""
    schema = [{"@type": "Service", "name": "Gold Service Plan", "serviceType": "HVAC maintenance plan", "url": abs_url(path), "provider": {"@id": f"{DOMAIN}/#business"},
               "description": "HVAC maintenance membership with two tune-ups a year, priority scheduling and 10% off repairs."}, breadcrumb_schema(crumbs), faq_schema(faqs)]
    page(path, "Gold Service Plan | HVAC Maintenance Plan in Kyle, TX",
         "Two HVAC tune-ups a year, priority scheduling and 10% off repairs. Climate Control Solutions' Gold Service Plan for Kyle, Buda & Austin homes.", main, schema, priority="0.9")

def build_town(t):
    crumbs = [("Home", ""), ("Service Area", "near-me/"), (f"{t['name']}, TX", t["path"])]
    local = [p for p in PROJECTS if p["town"] == t["key"] and p["images"]]
    others = [p for p in SHOWCASE if p["town"] != t["key"] and p["images"]]
    faqs = [FAQ[2], FAQ[1], FAQ[4]]
    name = t["name"]
    main = f"""{page_hero(crumbs, f'Heating & air conditioning in {name}, TX', esc(t['intro']), 'site/van', f'Climate Control Solutions service van in {name}, TX', eyebrow=f'{name} · {t["county"]}')}
<section class="section"><div class="wrap prose-split">
<div>{section_head(f'{name} HVAC services', f'Your local AC &amp; heating company in {esc(name)}')}
<div class="prose"><p>{esc(t['local'])}</p>
<p>When your AC stops cooling on a 100° afternoon or your heat quits during a cold snap, we'll diagnose the real problem, explain your options and fix it right. Emergency service is available 24/7 at <a href="tel:{B['phone_tel']}" data-call>{B['phone']}</a>.</p>
<p>We also install whole-home air quality products and offer the <a href="{url('gold-service-plan')}">Gold Service Plan</a> for {esc(name)} homeowners who want two tune-ups a year, priority scheduling and 10% off repairs.</p></div></div>
<aside class="side-card"><h3>Serving {esc(name)} 24/7</h3><p>Family-owned, based at {B['street']} in Kyle.</p>{cta_buttons('stack')}</aside>
</div></section>
<section class="section section-alt"><div class="wrap">{section_head('Services', f'What we do in {esc(name)}')}<div class="svc-grid">{service_cards()}</div></div></section>
{projects_section(local + others, h2=f'Recent work in {esc(name)}' if local else 'Recent installs &amp; repairs nearby', sub='Real jobs from our crew.' )}
{reviews_section(3, alt=True)}
{towns_section(exclude=t['key'])}
{faq_section(faqs, alt=True)}
{cta_band(f'Need HVAC help in {esc(name)}?')}"""
    schema = [{"@type": "Service", "name": f"HVAC services in {name}, TX", "serviceType": "Heating and air conditioning repair, replacement and maintenance",
               "url": abs_url(t["path"]), "provider": {"@id": f"{DOMAIN}/#business"}, "areaServed": {"@type": "City", "name": f"{name}, TX"}},
              business_node(), breadcrumb_schema(crumbs), faq_schema(faqs)]
    title = f"AC & Heating Repair in {name}, TX | Climate Control"
    if len(title) > 60: title = f"AC & Heating Repair in {name}, TX"
    page(t["path"], title, f"Heating & AC repair, replacement and maintenance in {name}, TX. Family-owned, 4.9★ on Google, 24/7 emergency service. Call (512) 960-5282.", main, schema, priority="0.8")

def build_area():
    path = "near-me/"
    crumbs = [("Home", ""), ("Service Area", path)]
    cards = "".join(f'<a class="town-card" href="{url(t["path"])}"><span>{icon("pin")}</span><h2>{esc(t["name"])}, TX</h2><p>{esc(t["intro"])}</p><span class="more">{esc(t["name"])} HVAC {icon("arrow")}</span></a>' for t in S["towns"])
    main = f"""{page_hero(crumbs, 'Our service area', f'Climate Control Solutions is based at {B["street"]} in Kyle and serves homes across Hays County and South Austin.', None)}
<section class="section"><div class="wrap"><div class="town-grid">{cards}</div></div></section>
{reviews_section(3, alt=True)}
{cta_band()}"""
    page(path, "HVAC Service Area | Kyle, Buda, Austin & Hays County",
         "Climate Control Solutions serves Kyle, Buda, Austin, San Marcos, Wimberley, Woodcreek, Dripping Springs, Driftwood, Mountain City and Hays, TX.",
         main, [business_node(), breadcrumb_schema(crumbs)], priority="0.8")

def build_projects():
    path = "projects/"
    crumbs = [("Home", ""), ("Projects", path)]
    main = f"""{page_hero(crumbs, 'Our projects', 'Real installs, replacements and repairs from our crew across Kyle, Buda, Wimberley, Dripping Springs and Austin.', None)}
<section class="section"><div class="wrap"><div class="proj-grid proj-grid-all">{project_cards(PROJECTS, 99)}</div>{brand_strip()}</div></section>
{reviews_section(3, alt=True)}
{cta_band()}"""
    page(path, "HVAC Projects in Kyle, Austin & Wimberley | Climate Control",
         "Photos of recent AC, heat pump, furnace and ductless installs and repairs by Climate Control Solutions in Kyle, Buda, Wimberley, Dripping Springs and Austin.",
         main, [breadcrumb_schema(crumbs)], priority="0.7")
    for i, p in enumerate(PROJECTS):
        build_project(p, PROJECTS[i + 1:] + PROJECTS[:i])

def build_project(p, others):
    path = "projects/" + p["slug"]
    crumbs = [("Home", ""), ("Projects", "projects/"), (p["title"], path)]
    town = TOWNS.get(p["town"])
    gallery = "".join(f'<a class="gal-item" href="{url("assets/img/" + im["name"] + "-" + str(im["widths"][-1]) + ".webp")}" data-lightbox>{img(im, p["title"] + f" photo {n + 1}", "(max-width:700px) 92vw, 50vw")}</a>' for n, im in enumerate(p["images"]))
    facts = []
    if town: facts.append(f'<li>{icon("pin")}<span><small>Location</small><a href="{url(town["path"])}">{esc(town["name"])}, TX</a></span></li>')
    if p["products"]: facts.append(f'<li>{icon("unit")}<span><small>Equipment</small>{esc(p["products"])}</span></li>')
    lede = "A recent project by the Climate Control Solutions team" + (f" in {esc(town['name'])}, TX" if town else "") + (f", featuring {esc(p['products'])} equipment." if p["products"] else ".")
    main = f"""{page_hero(crumbs, p['title'], lede, None, eyebrow='Project')}
<section class="section"><div class="wrap proj-detail">
<div class="gallery">{gallery}</div>
<div><div class="prose">{rebase(p['html'])}</div><ul class="facts">{''.join(facts)}</ul>
<aside class="side-card"><h3>Want results like this?</h3><p>Call for a new system estimate or book online.</p>{cta_buttons('stack')}</aside></div>
</div></section>
{projects_section(others, h2='More projects', alt=True)}
{cta_band()}"""
    title = p["title"] if len(p["title"]) > 38 else f"{p['title']} | Climate Control"
    first = p["images"][0] if p["images"] else None
    page(path, title[:60], (p["description"] or p["title"])[:155], main, [breadcrumb_schema(crumbs)], priority="0.5",
         og_image=img_url(first, first["widths"][-1]) if first else None, og_alt=p["title"])

def build_articles():
    path = "air-conditioning-tips/"
    crumbs = [("Home", ""), ("HVAC Tips", path)]
    main = f"""{page_hero(crumbs, 'HVAC tips for Central Texas homes', 'Practical advice from our team on keeping your AC and heating running through Texas summers and cold snaps.', None)}
<section class="section"><div class="wrap"><div class="art-grid art-grid-all">{article_cards(ARTICLES, 99)}</div></div></section>
{cta_band()}"""
    page(path, "HVAC Tips & Articles | Climate Control Solutions",
         "Heating and air conditioning advice for Kyle, Buda and Austin homeowners: tune-ups, filters, energy bills, and when to repair or replace.", main, [breadcrumb_schema(crumbs)], priority="0.6")
    for i, a in enumerate(ARTICLES):
        build_article(a, [x for x in ARTICLES if x is not a])

def build_article(a, others):
    path = "air-conditioning-tips/" + a["slug"]
    crumbs = [("Home", ""), ("HVAC Tips", "air-conditioning-tips/"), (a["title"], path)]
    hero_img = f'<figure class="art-hero">{img(a["image"], a["title"], "(max-width:760px) 92vw, 720px", eager=True)}</figure>' if a["image"] else ""
    main = f"""<section class="article-head"><div class="wrap narrow">{crumbs_html(crumbs)}<p class="eyebrow">HVAC tips</p><h1>{esc(a['title'])}</h1></div></section>
<article class="section article"><div class="wrap narrow">{hero_img}<div class="prose">{rebase(a['html'])}</div>
<aside class="side-card article-cta"><h3>Need a hand with your system?</h3><p>Our team serves Kyle, Buda, San Marcos and South Austin, with 24/7 emergency service.</p>{cta_buttons()}</aside>
</div></article>
<section class="section section-alt"><div class="wrap">{section_head('Keep reading', 'More HVAC tips')}<div class="art-grid scroller" data-swipe>{article_cards(others)}</div><p class="swipe-hint" aria-hidden="true">Swipe →</p></div></section>"""
    title = a["title"] if len(a["title"]) <= 60 else a["meta_title"] if 0 < len(a["meta_title"]) <= 60 else a["title"][:59].rsplit(" ", 1)[0]
    schema = [{"@type": "BlogPosting", "headline": a["title"][:110], "url": abs_url(path), "mainEntityOfPage": abs_url(path), "description": a["description"][:300],
               "author": {"@id": f"{DOMAIN}/#business"}, "publisher": {"@id": f"{DOMAIN}/#business"},
               **({"image": img_url(a["image"])} if a["image"] else {})}, business_node(), breadcrumb_schema(crumbs)]
    page(path, title, a["description"][:155], main, schema, priority="0.5",
         og_image=img_url(a["image"], a["image"]["widths"][-1]) if a["image"] else None, og_alt=a["title"])

def build_simple(path, h1, title, desc, inner, crumbs_label, priority="0.5", schema_extra=None, lede=""):
    crumbs = [("Home", ""), (crumbs_label, path)]
    main = f"""{page_hero(crumbs, h1, lede, None) if lede else f'<section class="article-head"><div class="wrap narrow">{crumbs_html(crumbs)}<h1>{esc(h1)}</h1></div></section>'}
{inner}"""
    page(path, title, desc, main, [breadcrumb_schema(crumbs)] + (schema_extra or []), priority=priority)

def build_about():
    inner = f"""<section class="section"><div class="wrap why">
<div class="why-media">{img('site/van', 'Climate Control Solutions service van', '(max-width:900px) 92vw, 40vw', 'why-img')}</div>
<div class="why-text">{section_head('Our story', 'Family-owned. Owner-led. Honest.')}
<div class="prose"><p>Climate Control Solutions is a family-owned and operated heating and air conditioning company based in Kyle, Texas. Our owner and service technician, Marcus, has more than a decade of experience in the HVAC industry and a passion for helping neighbors keep their systems running smoothly.</p>
<p>Every member of our team is licensed, insured and trained. We repair, replace and maintain AC and heating systems of every major brand, and we install whole-home air quality products for cleaner indoor air.</p>
<p>We earn our reviews the simple way: we show up on time, keep you updated, find the real problem and tell you the truth about it. If a repair will give you more good years, we'll recommend the repair. That's why so many of our {B['review_count']} Google reviews use the word <em>honest</em>.</p></div>
<ul class="checks">{''.join(f'<li>{icon("check")}<span>{x}</span></li>' for x in ['Texas ACR License ' + B['license'], '24/7 emergency service', 'All major brands and models', 'Financing available through FTL Finance'])}</ul>
</div></div></section>
{reviews_section(6, alt=True)}
{towns_section()}
{cta_band()}"""
    build_simple("about-us", "About Climate Control Solutions", "About Us | Family-Owned HVAC Company in Kyle, TX",
                 "Climate Control Solutions is a family-owned HVAC company in Kyle, TX, led by owner and technician Marcus. Licensed, insured and 4.9★ on Google.",
                 inner, "About", "0.7", [business_node()], lede="A family-owned heating and air conditioning company in Kyle, Texas, serving Hays County and South Austin.")

def build_faq():
    inner = faq_section(FAQ, h2="Heating & AC questions, answered", link_all=False) + cta_band("Still have a question?", f"Call {B['phone']} and talk to our team, or book online.")
    build_simple("faq", "Frequently asked questions", "HVAC FAQ | Climate Control Solutions, Kyle TX",
                 "Answers to common heating and AC questions: repair vs. replace, maintenance, emergency service, brands, financing and service area.",
                 inner, "FAQ", "0.7", [faq_schema(FAQ)], lede="Straight answers about AC and heating repair, replacement, maintenance and booking.")

def build_reviews():
    inner = f"""{reviews_section(len(S['reviews']), h2=f"{B['rating']} stars from {B['review_count']} Google reviews")}
<section class="section section-alt"><div class="wrap center-box"><h2>Had a great experience?</h2><p>Reviews help local families find an honest HVAC company. We'd be grateful for yours.</p>
<div class="btn-row center"><a class="btn btn-blue btn-lg" href="{B['google_write_review_url']}" target="_blank" rel="noopener">{icon('star')} Leave a Google review</a><a class="btn btn-ghost btn-lg" href="{B['google_reviews_url']}" target="_blank" rel="noopener">Read all reviews {icon('arrow')}</a></div></div></section>
{projects_section(SHOWCASE)}
{cta_band()}"""
    build_simple("reviews", "Customer reviews", "Reviews | Climate Control Solutions, 4.9★ on Google",
                 f"Read what Kyle, Buda and Austin homeowners say about Climate Control Solutions: {B['rating']} stars from {B['review_count']} Google reviews.",
                 inner, "Reviews", "0.7", lede=f"{B['rating']} stars from {B['review_count']} Google reviews (as of {B['rating_checked']}). Here's a sample in our customers' own words.")

def build_contact():
    inner = f"""<section class="section"><div class="wrap contact-grid">
<a class="contact-card cc-call" href="tel:{B['phone_tel']}" data-call>{icon('phone', 'i big')}<h2>Call us 24/7</h2><p class="cc-big">{B['phone']}</p><p>Emergency heating and AC service, day or night.</p></a>
<a class="contact-card cc-book" href="{B['booking_url']}" target="_blank" rel="noopener" data-book>{icon('calendar', 'i big')}<h2>Book online</h2><p class="cc-big">Pick a time</p><p>Schedule a repair, estimate or maintenance visit in a couple of minutes.</p></a>
<a class="contact-card cc-visit" href="{B['google_reviews_url']}" target="_blank" rel="noopener">{icon('pin', 'i big')}<h2>Our shop</h2><p class="cc-big">{B['street']}</p><p>{B['city']}, {B['region']} {B['zip']}. Open in Google Maps.</p></a>
</div>
<div class="wrap">{financing_strip()}</div></section>
{towns_section(alt=True)}
{faq_section([FAQ[9], FAQ[2], FAQ[3]])}"""
    build_simple("contact-us", "Contact Climate Control Solutions", "Contact Us | Climate Control Solutions, Kyle TX",
                 f"Call {B['phone']} for 24/7 heating and AC service, or book online. Climate Control Solutions, {B['street']}, Kyle, TX {B['zip']}.",
                 inner, "Contact", "0.7", [business_node(), faq_schema([FAQ[9], FAQ[2], FAQ[3]])], lede="Call any time, or book online and pick a time that works for you.")

def build_legal(key, h1, title):
    body = OLD[key]["html"]
    # old policy's contact block was template text (Hutto address); use the real business details
    body = re.sub(r"Climate Control Solutions Texas<br>.*?Hutto, Texas 78634", f"{B['name']}<br>{B['street']}<br>{B['city']}, {B['region']} {B['zip']}<br>{B['phone']}", body, flags=re.S)
    inner = f'<section class="section"><div class="wrap narrow"><div class="prose legal">{rebase(body)}</div></div></section>'
    build_simple(key, h1, title, f"{h1} for {B['name']} ({B['domain'].replace('https://', '')}).", inner, h1, "0.2")

def build_html_sitemap():
    groups = [("Main", [("Home", ""), ("About us", "about-us"), ("Reviews", "reviews"), ("FAQ", "faq"), ("Contact", "contact-us"), ("Gold Service Plan", "gold-service-plan")]),
              ("Services", [("Cooling services", "air-conditioning/"), ("Heating services", "heating/")] + [(s["name"], s["path"]) for s in S["services"]]),
              ("Service area", [("All areas", "near-me/")] + [(t["name"] + ", TX", t["path"]) for t in S["towns"]]),
              ("Projects", [("All projects", "projects/")] + [(p["title"], "projects/" + p["slug"]) for p in PROJECTS]),
              ("HVAC tips", [("All articles", "air-conditioning-tips/")] + [(a["title"], "air-conditioning-tips/" + a["slug"]) for a in ARTICLES])]
    li = lambda n, p: '<li><a href="' + url(p) + '">' + esc(n) + '</a></li>'
    cols = "".join(f'<div><h2 class="h3">{g}</h2><ul>{"".join(li(n, p) for n, p in items)}</ul></div>' for g, items in groups)
    inner = f'<section class="section"><div class="wrap sitemap-grid">{cols}</div></section>'
    build_simple("sitemap", "Sitemap", "Sitemap | Climate Control Solutions", "Every page on the Climate Control Solutions website.", inner, "Sitemap", "0.2")

def build_404():
    main = f"""<section class="page-hero"><div class="wrap ph-in"><div class="ph-text"><p class="eyebrow on-dark">Error 404</p><h1>This page blew a fuse.</h1>
<p class="lede">The page you're looking for moved or doesn't exist. Try one of these, or just give us a call.</p>{cta_buttons()}</div></div></section>
<section class="section"><div class="wrap"><div class="svc-grid">{service_cards()}</div></div></section>"""
    page("404", "Page not found | Climate Control Solutions", "This page could not be found.", main, [business_node(False)], sitemap=False)
    # GitHub Pages serves /404.html for unknown paths; links must work from any depth, so force absolute BASE links (already absolute).

# ---------- static + meta files ----------
def write_meta_files():
    (OUT / "robots.txt").write_text(
        ("User-agent: *\nAllow: /\n\nUser-agent: GPTBot\nAllow: /\n\nUser-agent: ClaudeBot\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /\n\nUser-agent: Google-Extended\nAllow: /\n\n"
         if LIVE else "User-agent: *\nDisallow: /\n\n") + f"Sitemap: {DOMAIN}/sitemap.xml\n")
    urls = "".join(f"<url><loc>{abs_url(p)}</loc><lastmod>{TODAY}</lastmod><priority>{pr}</priority></url>\n" for p, pr in PAGES)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    (OUT / "site.webmanifest").write_text(json.dumps({"name": B["name"], "short_name": "CC Solutions", "start_url": f"{BASE}/", "display": "standalone",
        "background_color": "#ffffff", "theme_color": "#0B1A33", "icons": [{"src": f"{BASE}/assets/logo-512.png", "sizes": "512x512", "type": "image/png"}]}, indent=1))
    svc = "\n".join(f"- {s['name']}: {abs_url(s['path'])}. {s['card']}" for s in S["services"])
    towns = "\n".join(f"- {t['name']}, TX: {abs_url(t['path'])}" for t in S["towns"])
    faq = "\n".join(f"Q: {f['q']}\nA: {f['a']}\n" for f in FAQ)
    (OUT / "llms.txt").write_text(f"""# {B['name']}

> Family-owned heating and air conditioning (HVAC) company based in Kyle, Texas. Repairs, replaces and maintains AC, furnaces and heat pumps of every major brand, installs indoor air quality products, and offers 24/7 emergency service across Kyle, Buda, San Marcos, Wimberley, Dripping Springs and South Austin.

- Phone: {B['phone']} (24/7 emergency service)
- Address: {B['street']}, {B['city']}, {B['region']} {B['zip']}
- Owner: {B['owner']}, owner and service technician with more than 10 years in HVAC
- License: Texas ACR contractor license {B['license']}
- Google rating: {B['rating']} stars from {B['review_count']} reviews (as of {B['rating_checked']}): {B['google_reviews_url']}
- Book online: {B['booking_url']}
- Financing: available through FTL Finance ({B['financing_url']})
- Brands serviced: {', '.join(B['brands'])}, and all other major brands

## Services
{svc}
- Gold Service Plan: {abs_url('gold-service-plan')}. Maintenance membership with two tune-ups a year (spring AC, fall heating), priority scheduling and 10% off repairs.

## Service area
{towns}

## Key pages
- Home: {abs_url()}
- About: {abs_url('about-us')}
- Reviews: {abs_url('reviews')}
- Projects (photos of real installs): {abs_url('projects/')}
- HVAC tips: {abs_url('air-conditioning-tips/')}
- FAQ: {abs_url('faq')}
- Contact: {abs_url('contact-us')}

## FAQ
{faq}""")
    (OUT / ".nojekyll").write_text("")

def copy_static():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    for d in ("css", "js", "assets"):
        shutil.copytree(ROOT / d, OUT / d)
    if LIVE and (ROOT / "CNAME").exists(): shutil.copy(ROOT / "CNAME", OUT / "CNAME")

def main():
    copy_static()
    build_home()
    build_hub("cooling", "air-conditioning/", "Air conditioning services", "AC Repair, Replacement & Maintenance | Kyle & Austin",
              "AC repair, new system installation and tune-ups in Kyle, Buda, San Marcos and South Austin. Every major brand, 24/7 emergency service.",
              "From a quick repair on a 100° afternoon to a new high-efficiency system, we keep Central Texas homes cool.", "site/condenser-stone")
    build_hub("heating", "heating/", "Heating services", "Heating Repair, Furnaces & Heat Pumps | Kyle & Austin",
              "Furnace and heat pump repair, replacement and maintenance in Kyle, Buda, San Marcos and South Austin. 24/7 emergency service.",
              "Furnaces and heat pumps repaired, replaced and tuned up so your heat works on the first cold night.", "projects/hvac-upgrade-austin-tx-1")
    for s in S["services"]: build_service(s)
    build_gold()
    build_area()
    for t in S["towns"]: build_town(t)
    build_projects()
    build_articles()
    build_about(); build_faq(); build_reviews(); build_contact()
    build_legal("privacy", "Privacy Policy", "Privacy Policy | Climate Control Solutions")
    build_legal("terms", "Terms of Use", "Terms of Use | Climate Control Solutions")
    build_html_sitemap()
    build_404()
    write_meta_files()
    print(f"Built {len(PAGES)} pages + 404 into docs/  (base='{BASE}', live={LIVE})")

if __name__ == "__main__":
    main()
