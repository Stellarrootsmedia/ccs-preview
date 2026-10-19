"""Check every built page: one H1, JSON-LD parses, FAQ schema count = visible FAQ count,
no duplicate ids, title/description lengths, internal links + assets resolve."""
import re, json, pathlib, sys
OUT = pathlib.Path(__file__).resolve().parent.parent / "docs"
BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else ""
problems = []
def exists(href):
    p = href.split("#")[0].split("?")[0]
    if BASE and p.startswith(BASE): p = p[len(BASE):]
    p = p.lstrip("/")
    return p == "" or (OUT / p).is_file() or (OUT / (p + ".html")).is_file() or (OUT / p / "index.html").is_file()
pages = sorted(OUT.rglob("*.html"))
for f in pages:
    s = f.read_text(); rel = f.relative_to(OUT)
    n_h1 = len(re.findall(r"<h1[\s>]", s))
    if n_h1 != 1: problems.append(f"{rel}: {n_h1} h1")
    for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try:
            d = json.loads(blk)
            for n in d.get("@graph", []):
                if n.get("@type") == "FAQPage":
                    vis = s.count('class="faq-item"')
                    if vis != len(n["mainEntity"]): problems.append(f"{rel}: FAQ schema {len(n['mainEntity'])} vs visible {vis}")
        except Exception as e: problems.append(f"{rel}: bad JSON-LD {e}")
    ids = re.findall(r'\sid="([^"]+)"', s)
    if len(ids) != len(set(ids)): problems.append(f"{rel}: duplicate ids")
    t = re.search(r"<title>(.*?)</title>", s).group(1)
    if len(t.replace("&amp;", "&")) > 60: problems.append(f"{rel}: title {len(t)} chars: {t}")
    d = re.search(r'name="description" content="([^"]*)"', s).group(1)
    if len(d.replace("&amp;", "&")) > 160: problems.append(f"{rel}: description {len(d)} chars")
    for h in re.findall(r'(?:href|src)="(/[^"]*)"', s) + [x.split()[0] for ss in re.findall(r'srcset="([^"]+)"', s) for x in ss.split(", ")]:
        if h.startswith("//"): continue
        if not exists(h): problems.append(f"{rel}: missing {h}")
print(f"{len(pages)} pages checked, {len(problems)} problems")
for p in sorted(set(problems)): print(" -", p)
