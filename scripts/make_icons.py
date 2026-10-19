"""Generate favicon PNGs, logo-512 and og-image.jpg. PYTHONPATH=/tmp/pil python3 scripts/make_icons.py"""
import pathlib
from PIL import Image, ImageDraw, ImageFont
ROOT = pathlib.Path(__file__).resolve().parent.parent
A = ROOT / "assets"
NAVY, RED, BLUE = (11, 26, 51), (254, 7, 0), (61, 116, 255)

def mark(size, bg=NAVY, radius=0.21, blue=BLUE):
    S = size * 4
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if bg: d.rounded_rectangle([0, 0, S - 1, S - 1], int(S * radius), fill=bg)
    k = S / 96; w = int(11 * k); cy = (12 + 36) * k; r = 26 * k
    for cx, col in ((34 * k, RED), (62 * k, blue)):
        d.arc([cx - r, cy - r, cx + r, cy + r], 45, 315, fill=col, width=w)
    return im.resize((size, size), Image.LANCZOS)

mark(64).save(A / "favicon-64.png")
mark(180, radius=0).save(A / "apple-touch-icon.png")
mark(512).save(A / "logo-512.png")

def font(sz, bold=True):
    for p in ["/System/Library/Fonts/Supplemental/Arial Black.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"] if bold else ["/System/Library/Fonts/Supplemental/Arial.ttf"]:
        try: return ImageFont.truetype(p, sz)
        except OSError: pass
    return ImageFont.load_default()

og = Image.new("RGB", (1200, 630), NAVY)
van = Image.open(ROOT / "_research/img/fbm-data/images/complete-hvac-services.jpg").convert("RGB")
vw = 520; van = van.resize((vw, int(van.height * vw / van.width)), Image.LANCZOS)
top = (van.height - 630) // 2 + 40
og.paste(van.crop((0, top, vw, top + 630)), (1200 - vw, 0))
d = ImageDraw.Draw(og)
d.rectangle([0, 622, 600, 630], fill=RED); d.rectangle([600, 622, 1200, 630], fill=(12, 72, 246))
og.paste(mark(96, bg=None), (60, 52), mark(96, bg=None))
d.text((168, 70), "CLIMATE CONTROL", font=font(30), fill="white")
d.text((168, 106), "SOLUTIONS", font=font(20, False), fill=(159, 176, 207))
d.text((60, 205), "Honest heating & AC", font=font(50), fill="white")
d.text((60, 268), "in Kyle, Buda &", font=font(50), fill="white")
d.text((60, 331), "South Austin", font=font(50), fill=(127, 164, 255))
d.text((60, 430), "★★★★★  4.9 from 662 Google reviews", font=font(26, False), fill=(242, 182, 52))
d.text((60, 478), "24/7 emergency service  ·  (512) 960-5282", font=font(26, False), fill=(201, 212, 234))
og.save(A / "og-image.jpg", quality=86, optimize=True)
print("icons + og-image written")
