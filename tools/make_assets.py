"""
Generuje PNG assety webu (výřezy postav, tvarové ořezy, placeholdery) do assets/img/.

Zdroj: assets/reference.png (návrhová koláž). Až budou k dispozici původní fotky,
stačí upravit SOURCES (cesta + výřez) a skript spustit znovu.

Instalace:  python -m pip install "rembg[cpu]" pillow numpy
Spuštění:   python tools/make_assets.py
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img"
REF = ROOT / "assets" / "reference.png"
SCALE = 2  # zdrojové výřezy jsou malé, zvětšíme je

OUT.mkdir(parents=True, exist_ok=True)
ref = Image.open(REF).convert("RGB")


# ---------- pomocné funkce ----------

def crop(box, scale=SCALE):
    c = ref.crop(box)
    c = c.resize((c.width * scale, c.height * scale), Image.LANCZOS)
    return c.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))


def clean_alpha(img, erase=()):
    """Zpevní masku z rembg, odstraní drobné zbytky a volitelně vymaže obdélníky."""
    a = img.getchannel("A")
    a = a.point(lambda v: 255 if v > 120 else 0)
    a = a.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))
    d = ImageDraw.Draw(a)
    for box in erase:
        d.rectangle(box, fill=0)
    # ponecháme jen největší souvislou oblast (postavu), zbytky koláže zmizí
    w, h = a.size
    seed = next((x, y) for y in range(h // 2, h) for x in [w // 2] if a.getpixel((x, y)) == 255)
    ImageDraw.floodfill(a, seed, 128)
    a = a.point(lambda v: 255 if v == 128 else 0)
    a = a.filter(ImageFilter.GaussianBlur(0.8))
    img.putalpha(a)
    return img


def sticker(img, border=14, color=(255, 255, 255, 255)):
    """Přidá bílý obrys jako u nalepovací samolepky."""
    pad = border + 4
    w, h = img.size
    canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    canvas.paste(img, (pad, pad), img)
    a = canvas.getchannel("A").point(lambda v: 255 if v > 30 else 0)
    grown = a.filter(ImageFilter.MaxFilter(border * 2 + 1)).filter(ImageFilter.GaussianBlur(1.2))
    base = Image.new("RGBA", canvas.size, color)
    base.putalpha(grown)
    base.alpha_composite(canvas)
    return base.crop(base.getbbox())


def mask_from(shape, size, seed=1):
    w, h = size
    m = Image.new("L", (w * 2, h * 2), 0)  # 2x supersampling kvůli hladkým hranám
    d = ImageDraw.Draw(m)
    W, H = w * 2, h * 2
    rnd = random.Random(seed)
    if shape == "blob":
        cx, cy, pts = W / 2, H / 2, []
        k = [rnd.uniform(0, math.tau) for _ in range(3)]
        for i in range(240):
            t = i / 240 * math.tau
            r = 1 + 0.09 * math.sin(3 * t + k[0]) + 0.06 * math.sin(5 * t + k[1]) + 0.04 * math.sin(2 * t + k[2])
            pts.append((cx + math.cos(t) * W * 0.43 * r, cy + math.sin(t) * H * 0.43 * r))
        d.polygon(pts, fill=255)
    elif shape == "circle":
        d.ellipse((4, 4, W - 4, H - 4), fill=255)
    elif shape == "arch":
        d.rounded_rectangle((0, 0, W, H), radius=24, fill=255)
        d.rectangle((0, 0, W, W // 2), fill=0)
        d.ellipse((0, 0, W, W), fill=255)
    elif shape == "stamp":
        r = max(W, H) // 48
        d.rectangle((0, 0, W, H), fill=255)
        for x in range(r, W, r * 3):
            d.ellipse((x - r, -r, x + r, r), fill=0)
            d.ellipse((x - r, H - r, x + r, H + r), fill=0)
        for y in range(r, H, r * 3):
            d.ellipse((-r, y - r, r, y + r), fill=0)
            d.ellipse((W - r, y - r, W + r, y + r), fill=0)
    elif shape == "torn":
        j = W // 40
        pts = []
        for x in range(0, W + 1, j):
            pts.append((x, rnd.uniform(0, j * 1.6)))
        for y in range(0, H + 1, j):
            pts.append((W - rnd.uniform(0, j * 1.6), y))
        for x in range(W, -1, -j):
            pts.append((x, H - rnd.uniform(0, j * 1.6)))
        for y in range(H, -1, -j):
            pts.append((rnd.uniform(0, j * 1.6), y))
        d.polygon(pts, fill=255)
    elif shape == "flower":
        cx, cy, pts = W / 2, H / 2, []
        for i in range(360):
            t = i / 360 * math.tau
            r = 0.44 + 0.04 * math.cos(9 * t)
            pts.append((cx + math.cos(t) * W * r, cy + math.sin(t) * H * r))
        d.polygon(pts, fill=255)
    return m.resize((w, h), Image.LANCZOS)


def shaped(img, shape, seed=1, border=12):
    img = img.convert("RGBA")
    if shape == "stamp":  # perforace musí být až na bílém okraji známky
        w, h = img.size
        card = Image.new("RGBA", (w + border * 3, h + border * 3), (255, 255, 255, 255))
        card.paste(img, (border * 3 // 2, border * 3 // 2))
        card.putalpha(mask_from("stamp", card.size, seed))
        return card
    img.putalpha(mask_from(shape, img.size, seed))
    return sticker(img, border)


def font(size, bold=True):
    for name in (["arialbd.ttf", "DejaVuSans-Bold.ttf"] if bold else ["arial.ttf", "DejaVuSans.ttf"]):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def placeholder(size, label, sub, bg, fg, shape, seed):
    """Hravý placeholder fotky – vzorek, ikona fotoaparátu, popisek."""
    w, h = size
    img = Image.new("RGBA", size, bg)
    d = ImageDraw.Draw(img)
    # tečkovaný „halftone“ vzorek
    for y in range(0, h, 22):
        for x in range((y // 22) % 2 * 11, w, 22):
            d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=fg + (40,))
    # fotoaparát
    cx, cy = w // 2, int(h * 0.42)
    d.rounded_rectangle((cx - 46, cy - 30, cx + 46, cy + 34), radius=12, outline=fg, width=6)
    d.rectangle((cx - 18, cy - 42, cx + 18, cy - 30), fill=fg)
    d.ellipse((cx - 18, cy - 16, cx + 18, cy + 20), outline=fg, width=6)
    f1, f2 = font(int(w * 0.06)), font(int(w * 0.07))
    tw = d.textlength(sub, font=f2)
    top = cy + 58
    d.rounded_rectangle((cx - tw / 2 - 18, top, cx + tw / 2 + 18, top + int(w * 0.07) + 26), radius=40, fill=(255, 255, 255))
    d.text((cx - tw / 2, top + 10), sub, font=f2, fill=fg)
    lw = d.textlength(label, font=f1)
    d.text((cx - lw / 2, cy - 92), label, font=f1, fill=fg)
    return shaped(img, shape, seed)


def save(img, name):
    path = OUT / name
    img.save(path, optimize=True)
    print(f"{name:28s} {img.size[0]}x{img.size[1]}  {path.stat().st_size // 1024} kB")


# ---------- výřezy postav (rembg) ----------
from rembg import new_session, remove  # noqa: E402

human = new_session("u2net_human_seg")
general = new_session("isnet-general-use")


def cutout(box, session=human, erase=(), border=14):
    img = remove(crop(box), session=session)
    img = clean_alpha(img, [tuple(v * SCALE for v in b) for b in erase])
    return sticker(img.crop(img.getbbox()), border)


# Marty ve svetru (hero vlevo v koláži) – vymažeme nalepenou vlajku
save(cutout((458, 150, 628, 362)), "marty-sweater.png")
# Marty v tričku – hlavní hero výřez
save(cutout((1064, 95, 1282, 412)), "marty-hero.png")
# Marty se sluchátky
save(cutout((240, 640, 356, 850), erase=[(0, 0, 8, 210)]), "marty-headphones.png")

# ---------- tvarové ořezy fotek ----------
save(shaped(crop((818, 645, 1030, 805)), "blob", seed=4), "marty-autumn-blob.png")
save(shaped(crop((634, 716, 744, 824)), "stamp", seed=2, border=14), "group-stamp.png")
save(shaped(crop((80, 866, 212, 1022)), "arch", seed=3), "marty-bridge-arch.png")
save(shaped(crop((845, 645, 995, 795)), "circle", seed=5), "marty-autumn-circle.png")
save(shaped(crop((1095, 125, 1245, 275)), "flower", seed=6), "marty-face-flower.png")
save(shaped(crop((1395, 80, 1505, 268)), "torn", seed=7), "bigben-torn.png")

# ---------- ilustrační samolepky z koláže ----------
save(cutout((402, 240, 460, 442), session=general, border=4), "bigben-sticker.png")
save(cutout((580, 360, 682, 442), session=general, border=4), "flag-sticker.png")

# ---------- placeholdery (až dorazí fotky, nahradit) ----------
PH = [
    ("ph-coffee.png", (420, 420), "FOTO", "Marty u kávy", (255, 228, 120), (120, 82, 10), "blob", 11),
    ("ph-travel.png", (380, 460), "FOTO", "Na cestách", (188, 220, 246), (24, 74, 120), "stamp", 12),
    ("ph-online.png", (400, 400), "FOTO", "Online lekce", (220, 194, 251), (82, 40, 130), "circle", 13),
    ("ph-olomouc.png", (460, 360), "FOTO", "Olomouc", (245, 198, 228), (130, 30, 90), "torn", 14),
    ("ph-group.png", (380, 480), "FOTO", "Skupinovka", (190, 232, 210), (8, 90, 66), "arch", 15),
    ("ph-books.png", (400, 400), "FOTO", "Oblíbené knížky", (255, 210, 180), (140, 60, 20), "flower", 16),
]
for name, size, label, sub, bg, fg, shape, seed in PH:
    save(placeholder(size, label, sub, bg, fg, shape, seed), name)
