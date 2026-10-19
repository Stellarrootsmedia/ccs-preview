"""One-time: pull clean content out of the old Uplift pages into data/old_content.json."""
import re, json, html, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ROOT / "_research" / "pages"
out = {}
KEEP = {"h1","h2","h3","h4","p","ul","ol","li","strong","em","b","i","a","img","br","blockquote","table","tr","td","th","thead","tbody"}

def clean(fragment):
    f = re.sub(r"(?s)<!--.*?-->|<script.*?</script>|<style.*?</style>|<svg.*?</svg>|<noscript.*?</noscript>", "", fragment)
    f = re.sub(r'(?s)<div class="breadcrumb[^"]*">(?:\s*<div class="breadcrumb-item[^>]*>.*?</div>)*\s*</div>', "", f)  # drop breadcrumb
    f = re.sub(r"(?s)<h2[^>]*>\s*Recent Articles.*$", "", f)
    def tag(m):
        close, name, attrs = m.group(1), m.group(2).lower(), m.group(3) or ""
        if name not in KEEP: return ""
        if close: return f"</{name}>"
        if name == "a":
            h = re.search(r'href="([^"]*)"', attrs)
            return f'<a href="{h.group(1)}">' if h else "<a>"
        if name == "img":
            s = re.search(r'src="([^"]*)"', attrs); a = re.search(r'alt="([^"]*)"', attrs)
            return f'<img src="{s.group(1) if s else ""}" alt="{a.group(1) if a else ""}">'
        return f"<{name}>"
    f = re.sub(r"<(/?)([a-zA-Z0-9]+)([^>]*)>", tag, f)
    f = re.sub(r"[ \t]+", " ", f); f = re.sub(r"\s*\n\s*", "\n", f)
    f = re.sub(r"<p>\s*</p>|<a>\s*</a>|<h2>\s*</h2>", "", f)
    f = re.sub(r"(?s)^.*?(?=<h1>)", "", f, count=1) if "<h1>" in f else f
    return f.strip()

for fp in sorted(PAGES.glob("*.html")):
    s = fp.read_text(errors="ignore")
    title = html.unescape(re.search(r"<title>(.*?)</title>", s, re.S).group(1).strip()) if "<title>" in s else ""
    d = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', s) or re.search(r'<meta[^>]+content="([^"]*)"[^>]+name="description"', s)
    a = s.find("<main")
    ends = [i for i in (s.find(m, a) for m in ("END PAGE CONTENTS", "START MOBILE CTA", "START LATEST", "Our Latest Projects", "Need a Professional HVAC Installer", "</main>")) if i > a]
    body = clean(s[a:min(ends)]) if a > 0 else ""
    h1 = re.search(r"<h1>(.*?)</h1>", body, re.S)
    date = re.search(r'(?:datePublished|"date")"?\s*:\s*"([^"]+)"', s) or re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}", body)
    imgs = re.findall(r'src="(/fbm-data/[^"]+)"', body)
    body_noh1 = re.sub(r"(?s)<h1>.*?</h1>", "", body, count=1)
    out[fp.stem] = {"title": title, "description": html.unescape(d.group(1)) if d else "",
                    "h1": html.unescape(re.sub("<[^>]+>", "", h1.group(1)).strip()) if h1 else "",
                    "date": (date.group(1) if date and date.lastindex == 1 and "datePublished" in date.group(0) else (date.group(0) if date else "")),
                    "images": imgs, "html": body_noh1}
(ROOT / "data").mkdir(exist_ok=True)
(ROOT / "data" / "old_content.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
for k, v in out.items(): print(f"{k[:55]:55} h1={v['h1'][:45]!r} len={len(v['html'])} imgs={len(v['images'])} date={v['date']!r}")
