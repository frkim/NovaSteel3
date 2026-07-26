"""Generate original, editable-support visual assets for the NovaSteel deck."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math
import random

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

CARBON = (18, 23, 25)
COAL = (31, 36, 38)
STEEL = (120, 136, 139)
LIGHT_STEEL = (213, 220, 218)
RUST = (182, 74, 45)
AMBER = (227, 167, 47)
TEAL = (20, 125, 116)


def steelworks_hero() -> None:
    width, height = 1920, 1080
    img = Image.new("RGB", (width, height), CARBON)
    px = img.load()
    random.seed(240725)
    for y in range(height):
        t = y / height
        base = tuple(int(CARBON[i] * (1 - t) + COAL[i] * t) for i in range(3))
        for x in range(width):
            grain = random.choice((-2, -1, 0, 0, 0, 1))
            px[x, y] = tuple(max(0, min(255, c + grain)) for c in base)

    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((900, 250, 1600, 950), fill=(219, 80, 35, 130))
    gd.ellipse((1030, 390, 1500, 860), fill=(245, 169, 44, 150))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img = Image.alpha_composite(img.convert("RGBA"), glow)

    draw = ImageDraw.Draw(img)
    # Ground and plant silhouette.
    draw.rectangle((0, 835, width, height), fill=(13, 17, 18, 255))
    for x in (185, 430, 1435, 1690):
        stack_w = 65 if x != 430 else 90
        stack_h = 250 if x != 430 else 360
        draw.polygon(
            [(x, 835), (x + stack_w, 835), (x + stack_w - 16, 835 - stack_h),
             (x + 16, 835 - stack_h)],
            fill=(52, 60, 61, 255),
        )
        draw.rectangle((x + 10, 835 - stack_h + 55, x + stack_w - 10, 835 - stack_h + 66),
                       fill=(182, 74, 45, 220))
    draw.rectangle((620, 635, 1295, 840), fill=(45, 52, 53, 255))
    draw.polygon([(720, 635), (1195, 635), (1325, 760), (590, 760)], fill=(61, 70, 70, 255))
    draw.ellipse((840, 665, 1130, 955), fill=(28, 30, 29, 255), outline=(227, 167, 47, 255), width=9)
    draw.ellipse((900, 725, 1070, 895), fill=(136, 53, 31, 255))
    draw.ellipse((933, 758, 1037, 862), fill=(232, 151, 43, 255))
    # Steel truss / crane geometry.
    for x in range(0, width, 160):
        draw.line((x, 120, x + 280, 835), fill=(86, 97, 96, 135), width=8)
        draw.line((x + 280, 120, x + 20, 835), fill=(86, 97, 96, 115), width=5)
    draw.line((0, 170, width, 170), fill=(122, 136, 139, 150), width=14)
    draw.line((0, 825, width, 825), fill=(182, 74, 45, 200), width=4)
    img.convert("RGB").save(ASSETS / "steelworks-hero.png", quality=94)


def thermal_map() -> None:
    width, height = 1200, 700
    img = Image.new("RGB", (width, height), (24, 29, 31))
    draw = ImageDraw.Draw(img)
    cx, cy = 510, 350
    outer, inner = 290, 120
    for sector in range(12):
        a0 = math.radians(-90 + sector * 30 + 1)
        a1 = math.radians(-90 + (sector + 1) * 30 - 1)
        pts = [(cx, cy)]
        for r, count in ((outer, 10), (inner, 10)):
            angles = [a0 + (a1 - a0) * i / (count - 1) for i in range(count)]
            ring = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in angles]
            if r == outer:
                pts.extend(ring)
            else:
                pts.extend(reversed(ring))
        if sector == 6:
            color = (219, 77, 43)
        elif sector in (5, 7):
            color = (185, 102, 46)
        else:
            color = (48 + sector * 3, 87 + sector * 2, 89 + sector * 2)
        draw.polygon(pts, fill=color, outline=(213, 220, 218))
    draw.ellipse((cx - inner, cy - inner, cx + inner, cy + inner), fill=(22, 26, 28), outline=(213, 220, 218), width=3)
    for sector in range(12):
        angle = math.radians(-90 + sector * 30 + 15)
        tx = cx + 205 * math.cos(angle)
        ty = cy + 205 * math.sin(angle)
        draw.text((tx - 15, ty - 10), f"{sector + 1:02}", fill=(245, 240, 233))
    draw.rounded_rectangle((840, 120, 1120, 515), radius=20, fill=(34, 40, 41), outline=(182, 74, 45), width=4)
    draw.text((880, 165), "HEARTH", fill=(213, 220, 218))
    draw.text((880, 215), "SECTOR 07", fill=(245, 240, 233))
    draw.text((880, 300), "WARM ZONE", fill=(227, 167, 47))
    draw.text((880, 358), "Synthetic", fill=(213, 220, 218))
    draw.text((880, 390), "evidence", fill=(213, 220, 218))
    img.save(ASSETS / "thermal-map.png")


def steel_texture() -> None:
    width, height = 1600, 900
    img = Image.new("RGB", (width, height), (24, 29, 31))
    draw = ImageDraw.Draw(img)
    random.seed(2307)
    for i in range(120):
        x = random.randint(0, width)
        y = random.randint(0, height)
        length = random.randint(90, 360)
        alpha = random.randint(15, 45)
        shade = (40 + alpha, 47 + alpha, 48 + alpha)
        draw.line((x, y, min(width, x + length), max(0, y - length // 8)), fill=shade, width=random.randint(1, 3))
    for x in range(-300, width + 300, 180):
        draw.line((x, 0, x - 260, height), fill=(47, 55, 55), width=2)
    img.save(ASSETS / "steel-texture.png")


if __name__ == "__main__":
    steelworks_hero()
    thermal_map()
    steel_texture()
    print(f"Generated assets in {ASSETS}")
