"""Generate the annotated screenshots referenced by ``docs\\demo\\demo-runbook.md``.

Sources are the first-party application captures in
``docs\\presentation\\assets\\app-guide\\screenshots``. Each output crops the empty
tail of the full-page capture, scales it down for the runbook, and draws a red
frame plus a numbered caption tab around the exact region the presenter must
point at.

Run with the repository's Python (Pillow is the only dependency; restore it from
the Microsoft-protected feed only, see ``docs\\tech\\security_requirement.md``)::

    python tools\\presentation\\annotate_demo_screenshots.py

Nothing is downloaded and no third-party imagery is introduced: the script only
re-renders captures that already live in this repository.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "docs" / "presentation" / "assets" / "app-guide" / "screenshots"
OUTPUT_DIR = ROOT / "docs" / "demo" / "screenshots"

TARGET_WIDTH = 1400
RED = (208, 26, 26)
WHITE = (255, 255, 255)

FONT_CANDIDATES = (
    "seguisb.ttf",
    "arialbd.ttf",
    "DejaVuSans-Bold.ttf",
    "LiberationSans-Bold.ttf",
)


@dataclass(frozen=True)
class Box:
    """A highlight rectangle expressed in *source* pixel coordinates."""

    label: str
    left: int
    top: int
    right: int
    bottom: int
    below: bool = False  # place the caption tab under the frame instead of above
    align_right: bool = False  # pin the caption tab to the right edge of the frame


@dataclass(frozen=True)
class Shot:
    name: str
    source: str
    crop_bottom: int | None = None
    boxes: tuple[Box, ...] = field(default_factory=tuple)


SHOTS: tuple[Shot, ...] = (
    Shot(
        "s1-axelormetal-home",
        "company-website-home.png",
        1750,
        (
            Box("1 · Public-site tabs frame the fictitious company", 320, 380, 1010, 430, below=True),
            Box("2 · AxelorMetal operates the plant; NovaSteel is the platform", 456, 700, 1640, 950),
        ),
    ),
    Shot(
        "s2-command-center",
        "command-center-overview.png",
        1830,
        (
            Box("1 · Site status — select Moselle Integrated Works", 304, 430, 2060, 550),
            Box("2 · Energy, CO2, lining RUL, yield and open alerts", 304, 915, 2060, 1125),
        ),
    ),
    Shot(
        "s3-fabric-core",
        "adaptive-cloud-iot-operations.png",
        None,
        (
            Box("1 · Edge capture keeps the event-time envelope", 385, 138, 990, 215),
            Box("2 · One governed Fabric core: RTI, ontology, dashboards", 1105, 225, 1575, 510),
        ),
    ),
    Shot(
        "s4-energy-spot-price",
        "energy-optimization-spot-price-schedule.png",
        2000,
        (
            Box("1 · 280 EUR/MWh evening scarcity peak", 320, 515, 750, 700),
            Box("2 · Baseline dispatch sits on top of the price peak", 1500, 825, 1775, 1150, below=True),
        ),
    ),
    Shot(
        "s5-energy-optimized",
        "energy-optimization-load-shift-simulator.png",
        1320,
        (
            Box("1 · Modeled saving, peak reduction, zero hard violations", 320, 515, 2060, 665),
            Box("2 · Baseline vs optimized — 960 t tonnage conserved", 320, 800, 1600, 1230, below=True),
        ),
    ),
    Shot(
        "s6-thermal-explorer",
        "furnace-health-thermal-explorer.png",
        1300,
        (
            Box("1 · SECTOR-07 warm zone, cells at or above 700 C", 425, 935, 1580, 1015),
            Box("2 · Neighbours, cooling dT and heat flux agree", 1595, 820, 2060, 1165, below=True),
        ),
    ),
    Shot(
        "s7-lining-forecast",
        "furnace-health-lining-forecast.png",
        1350,
        (
            Box("1 · P50 19.7 d, P10-P90 18.69-20.61", 745, 515, 1610, 665),
            Box("2 · Risk crosses the 0.8 threshold near day 19.7", 1090, 845, 1450, 1165),
            Box("3 · Hand-off to a synthetic work order — no actuation", 1610, 1225, 2055, 1280, below=True),
        ),
    ),
    Shot(
        "s8-copilot-grounding",
        "feature-copilot-panel.png",
        1900,
        (
            Box("1 · Copilot docks right and reads the current screen", 1530, 410, 2070, 700),
            Box("2 · Answers stay inside the synthetic demo grounding", 1545, 1650, 2070, 1780, below=True),
        ),
    ),
    Shot(
        "s9-maintenance-workorder",
        "furnace-health-maintenance-planner.png",
        1650,
        (
            Box("1 · Relining window 18-24 d aligns with the RUL", 745, 515, 1610, 665),
            Box("2 · WO-DEMO-LUX-1042 — synthetic planned inspection", 320, 1460, 2060, 1565, below=True),
        ),
    ),
    Shot(
        "s10-quality-genealogy",
        "quality-batches.png",
        1960,
        (
            Box("1 · Predicted first-pass yield against target", 320, 515, 1190, 700),
            Box("2 · Downward excursion flags the drifting DP780 coil", 825, 825, 1550, 1150, below=True),
            Box("3 · Heat, coil, coiling bias and result in one genealogy", 320, 1490, 2060, 1935, below=True),
        ),
    ),
    Shot(
        "s11-quality-spc",
        "quality-spc.png",
        1300,
        (
            Box("1 · Cpk 1.18 with one special-cause signal", 320, 515, 1190, 665),
            Box("2 · Out-of-control point breaches the upper limit", 1480, 820, 1610, 950),
        ),
    ),
    Shot(
        "s12-knowledge-capture",
        "knowledge-hub-capture-status.png",
        1660,
        (
            Box("1 · Draft extracted from the interview, cited to source", 755, 955, 1195, 1180),
            Box("2 · Human-in-the-loop gate before publication", 1590, 1240, 2065, 1610, below=True),
        ),
    ),
    Shot(
        "s13-sustainability-ets",
        "sustainability-ets-exposure.png",
        1270,
        (
            Box("1 · ETS exposure — modeled targets, not commitments", 320, 515, 2060, 665),
            Box("2 · Allowance use projected to breach the cap in month 5", 1090, 820, 1610, 950),
        ),
    ),
    Shot(
        "s14-audit-trail",
        "sustainability-audit.png",
        1250,
        (
            Box("1 · Model-linked and append-only decision evidence", 1195, 515, 2065, 665),
            Box("2 · Actor, action, model version, correlation, audit ref", 320, 990, 2060, 1165, below=True),
        ),
    ),
    Shot(
        "s15-executive-overview",
        "executive-overview.png",
        1300,
        (
            Box("1 · 14 / 22 / 8 / 21 are targets, not measured outcomes", 320, 515, 2060, 665),
            Box("2 · Target versus actual roll-up with proof badges", 1590, 785, 2065, 975, below=True),
        ),
    ),
    Shot(
        "s16-help-explain-mode",
        "feature-help-assistant.png",
        1350,
        (
            Box("2 · The ? toggle in the dashboard header", 1590, 245, 1740, 300),
            Box("1 · Explain mode banner is active", 850, 10, 1235, 75, below=True, align_right=True),
            Box("3 · Click any KPI, chart or table row for a topic popup", 320, 515, 750, 665, below=True),
        ),
    ),
    Shot(
        "s17-device-fleet",
        "device-operations-fleet.png",
        1700,
        (
            Box("1 · 6 devices, 1 degraded, mean health score", 320, 520, 2060, 665),
            Box("2 · LUX-BF-01 is pre-armed as degraded", 320, 1525, 2060, 1610, below=True),
        ),
    ),
    Shot(
        "s18-sensor-explorer",
        "device-operations-sensors.png",
        1500,
        (
            Box("1 · Device and status filters — pre-filter to LUX-BF-01", 300, 545, 810, 620),
            Box("2 · Status, trend and deviation % per sensor", 1040, 700, 1780, 1400, below=True),
        ),
    ),
    Shot(
        "s19-device-simulator",
        "device-operations-simulator.png",
        1950,
        (
            Box("1 · Simulator state, scenario, speed and seed", 320, 520, 2060, 665),
            Box("2 · Active incidents progress in the in-process ring buffer", 320, 1155, 2060, 1510),
            Box("3 · Trigger and Clear act on synthetic signals only", 320, 1570, 2060, 1910),
        ),
    ),
)


def _font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def _draw_frame(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    left, top, right, bottom = box
    draw.rounded_rectangle((left - 3, top - 3, right + 3, bottom + 3), radius=10, outline=WHITE, width=7)
    draw.rounded_rectangle((left, top, right, bottom), radius=8, outline=RED, width=4)


def _draw_tab(draw: ImageDraw.ImageDraw, box: Box, scaled: tuple[int, int, int, int], size: tuple[int, int]) -> None:
    left, top, right, bottom = scaled
    width, height = size
    font = _font(22)
    text_w = int(draw.textlength(box.label, font=font))
    tab_w, tab_h = text_w + 26, 36
    anchor_x = right - tab_w if box.align_right else left
    tab_x = min(max(anchor_x, 6), width - tab_w - 6)
    tab_y = bottom + 8 if box.below else top - tab_h - 8
    if tab_y < 4:
        tab_y = bottom + 8
    if tab_y + tab_h > height - 4:
        tab_y = max(4, top - tab_h - 8)
    draw.rounded_rectangle((tab_x, tab_y, tab_x + tab_w, tab_y + tab_h), radius=8, fill=RED)
    draw.text((tab_x + 13, tab_y + tab_h / 2), box.label, font=font, fill=WHITE, anchor="lm")


def render(shot: Shot) -> Path:
    source = SOURCE_DIR / shot.source
    image = Image.open(source).convert("RGB")
    width, height = image.size
    bottom = min(shot.crop_bottom or height, height)
    image = image.crop((0, 0, width, bottom))

    scale = TARGET_WIDTH / width
    image = image.resize((TARGET_WIDTH, round(bottom * scale)), Image.LANCZOS)
    draw = ImageDraw.Draw(image)

    for box in shot.boxes:
        scaled = (
            round(box.left * scale),
            round(box.top * scale),
            round(box.right * scale),
            round(box.bottom * scale),
        )
        _draw_frame(draw, scaled)
        _draw_tab(draw, box, scaled, image.size)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUTPUT_DIR / f"{shot.name}.png"
    image.save(target, optimize=True)
    return target


def main() -> None:
    missing = [shot.source for shot in SHOTS if not (SOURCE_DIR / shot.source).is_file()]
    if missing:
        raise SystemExit(f"Missing source captures: {', '.join(sorted(set(missing)))}")
    for shot in SHOTS:
        target = render(shot)
        print(f"{target.relative_to(ROOT)}  <- {shot.source}")


if __name__ == "__main__":
    main()
