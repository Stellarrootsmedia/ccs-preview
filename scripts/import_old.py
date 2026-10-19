"""One-time: turn data/old_content.json into data/projects.json + data/articles.json and
convert their photos (plus site photos) to responsive WebP in assets/img/.
Needs Pillow:  PYTHONPATH=/tmp/pil python3 scripts/import_old.py"""
import re, json, html, pathlib
from PIL import Image, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
OLD = ROOT / "_research" / "img"
OUT = ROOT / "assets" / "img"
old = json.loads((ROOT / "data" / "old_content.json").read_text())
order = [l.strip().replace("https://www.ccsolutionsatx.com/", "") for l in (ROOT / "_research" / "old-urls.txt").read_text().split()]
WIDTHS = (480, 960, 1440)

def webp(src_rel, name, widths=WIDTHS):
    """Write name-<w>.webp for each width <= original; return {"src","w","h","sizes":[...]}."""
    p = OLD / src_rel.lstrip("/")
    if not p.exists():
        p = OLD / src_rel.lstrip("/").replace("/thumbs", "")
    im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    W, H = im.size
    made = []
    for w in widths:
        w2 = min(w, W)
        if w2 in made: break
        out = OUT / f"{name}-{w2}.webp"
        out.parent.mkdir(parents=True, exist_ok=True)
        im.resize((w2, round(H * w2 / W)), Image.LANCZOS).save(out, "WEBP", quality=78, method=6)
        made.append(w2)
        if w2 == W: break
    return {"name": name, "w": W, "h": H, "widths": made}

def text_of(h):
    return html.unescape(re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", h))).strip()

def tidy(h):
    h = re.sub(r"<!--.*$", "", h, flags=re.S)
    h = re.sub(r"<a>\s*<i></i>[^<]*</a>|<i></i>", "", h)
    h = h.replace("&#039;", "'")
    return h.strip()

TOWN_SLUGS = {"kyle": "kyle", "buda": "buda", "austin": "austin", "ausin": "austin", "wimberley": "wimberley", "wimberly": "wimberley",
              "dripping-springs": "dripping-springs", "san-marcos": "san-marcos", "driftwood": "driftwood"}

projects = []
for i, key in enumerate(order):
    if not key.startswith("projects/") or key == "projects/": continue
    c = old[key.replace("/", "__")]
    slug = key.split("/", 1)[1]
    body = tidy(c["html"])
    full = re.findall(r'<a href="(/(?:fbm|uplift)-data/images/[^"]+)">\s*<img', body)
    inline = re.findall(r'<img src="(/(?:fbm|uplift)-data/images/[^"]+)"', body)
    srcs = list(dict.fromkeys(full + [s for s in inline if "/thumbs/" not in s] + [s.replace("/thumbs", "") for s in inline if "/thumbs/" in s]))
    if not srcs:  # some pages keep the photo outside the content block
        raw = (ROOT / "_research" / "pages" / (key.replace("/", "__") + ".html")).read_text(errors="ignore")
        srcs = [s for s in dict.fromkeys(re.findall(r'(/(?:fbm|uplift)-data/images/projects/[^"/]+\.(?:jpe?g|png))', raw))]
    srcs = [s for s in srcs if (OLD / s.lstrip("/")).exists()]
    products = re.search(r"<h2>Products Used</h2>\s*<ul>(.*?)</ul>", body, re.S)
    intro = re.split(r"<h2>|<p>\s*<strong>Location", body)[0]
    intro = re.sub(r"<img[^>]*>|<a href=\"/(?:fbm|uplift)-data[^\"]*\">\s*</a>", "", intro).strip()
    loc = re.search(r'Location: </strong><a href="/near-me/([^"]+)"', body)
    town = next((v for k, v in TOWN_SLUGS.items() if k in (slug + (loc.group(1) if loc else "")).lower()), "")
    imgs = [webp(s, f"projects/{slug.lower()}-{n+1}") for n, s in enumerate(srcs)]
    projects.append({"slug": slug, "title": c["h1"], "meta_title": c["title"], "description": c["description"] or text_of(intro)[:150],
                     "town": town, "products": text_of(products.group(1)) if products else "", "html": intro, "images": imgs, "order": i})
projects.sort(key=lambda p: -p["order"])

articles = []
for i, key in enumerate(order):
    if not key.startswith("air-conditioning-tips/") or key == "air-conditioning-tips/": continue
    c = old[key.replace("/", "__")]
    slug = key.split("/", 1)[1]
    body = tidy(c["html"])
    m = re.search(r'<img src="(/(?:fbm|uplift)-data/images/[^"]+)"', body)
    img = webp(m.group(1), f"articles/{slug}", (480, 960)) if m and (OLD / m.group(1).lstrip("/")).exists() else None
    body = re.sub(r"<img[^>]*>", "", body, count=1).strip()
    first_p = re.search(r"<p>(.*?)</p>", body, re.S)
    articles.append({"slug": slug, "title": c["h1"], "meta_title": c["title"], "description": c["description"] or text_of(first_p.group(1))[:155],
                     "excerpt": text_of(first_p.group(1))[:220] if first_p else "", "html": body, "image": img, "order": i})
articles.sort(key=lambda a: -a["order"])

(ROOT / "data" / "projects.json").write_text(json.dumps(projects, indent=1, ensure_ascii=False))
(ROOT / "data" / "articles.json").write_text(json.dumps(articles, indent=1, ensure_ascii=False))

# Site photos used by templates
SITE = {
    "/fbm-data/images/complete-hvac-services.jpg": "site/van",
    "/fbm-data/images/complete-services-2.jpg": "site/condenser-stone",
    "/fbm-data/images/banner/banner-main-new-2.jpg": "site/condensers",
    "/fbm-data/images/services/ac-replacement-page.jpg": "site/ac-replacement",
    "/fbm-data/images/services/heating-repair-page.jpg": "site/heating-repair",
    "/fbm-data/images/services/heating-replacement-page.jpg": "site/heating-replacement",
    "/fbm-data/images/services/ac-repair-page.jpg": "site/ac-repair",
    "/fbm-data/images/services/ac-maintenance-page.jpg": "site/ac-maintenance",
    "/fbm-data/images/services/heating-maintenance-page.jpg": "site/heating-maintenance",
    "/fbm-data/images/services/air-quality-page.jpg": "site/air-quality",
    "/uplift-data/images/services/gold-service-plan.jpg": "site/gold-plan",
}
site = {v: webp(k, v) for k, v in SITE.items()}
(ROOT / "data" / "images.json").write_text(json.dumps(site, indent=1))
print(len(projects), "projects,", len(articles), "articles,", len(site), "site photos")
for p in projects: print(" ", p["slug"], p["town"], len(p["images"]), "imgs |", p["products"])
