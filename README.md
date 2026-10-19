# Climate Control Solutions website

Static rebuild of ccsolutionsatx.com. Every old URL is kept (59 pages), generated from data files.

## Edit content
- `data/site.json`: business info, rating/review count, reviews, FAQ, service pages, town pages, tracking IDs
- `data/projects.json`, `data/articles.json`: projects and HVAC tips (imported from the old site)
- Layout: `scripts/build.py` (templates) + `css/styles.css` (all colors/fonts are variables in `:root`)

## Build
    python3 scripts/build.py --base /ccs-preview   # GitHub Pages preview (noindex, no tracking)
    python3 scripts/build.py --live                # production: GTM + Meta Pixel on, indexable, CNAME
    python3 scripts/validate.py /ccs-preview       # checks H1s, schema, FAQ counts, links, title lengths

Output goes to `docs/` (served by GitHub Pages). Bump `V` in build.py when CSS/JS change.
Images: `PYTHONPATH=/tmp/pil python3 scripts/import_old.py` regenerates WebP from `_research/` (not in git).
