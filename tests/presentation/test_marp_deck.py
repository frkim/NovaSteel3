"""Structural validation for the Marp deck under ``presentation/``.

The deck is generated in CI (``.github/workflows/presentation.yml``) straight from
``presentation/slides.md``. These checks keep that source buildable and keep the
30-minute speaking budget honest before a single browser is started.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PRESENTATION = ROOT / "presentation"
SLIDES = PRESENTATION / "slides.md"
THEME = PRESENTATION / "theme.css"

MAIN_SLIDE_COUNT = 22
BACKUP_SLIDE_COUNT = 12
MIN_TALK_SECONDS = 29 * 60
MAX_TALK_SECONDS = 30 * 60

NOTE_PATTERN = re.compile(r"<!--(?!\s*_)(.*?)-->", re.DOTALL)
TIMING_PATTERN = re.compile(r"^\s*⏱\s*(\d+):([0-5]\d)\s*·\s")
SCOPED_CLASS_PATTERN = re.compile(r"<!--\s*_class:\s*(.*?)\s*-->")
HTML_CLASS_PATTERN = re.compile(r'class="([^"]+)"')
IMAGE_PATTERN = re.compile(r"!\[[^\]]*\]\(images/([^)]+)\)")
PLACEHOLDERS = ("TODO", "TBD", "FIXME", "Lorem ipsum", "XXX")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _front_matter_and_slides() -> tuple[str, list[str]]:
    text = _read(SLIDES)
    parts = re.split(r"(?m)^---\s*$", text)
    assert parts[0].strip() == "", "slides.md must start with the Marp front matter"
    return parts[1], list(parts[2:])


def _duration_seconds(note: str) -> int:
    match = TIMING_PATTERN.match(note.strip())
    assert match is not None, f"speaker note is missing its timing marker: {note.strip()[:80]!r}"
    return int(match.group(1)) * 60 + int(match.group(2))


def _classes(slide: str) -> set[str]:
    names: set[str] = set()
    for value in SCOPED_CLASS_PATTERN.findall(slide):
        names.update(value.split())
    return names


def test_front_matter_declares_the_novasteel_marp_theme() -> None:
    front_matter, _ = _front_matter_and_slides()
    assert "marp: true" in front_matter
    assert "theme: novasteel" in front_matter
    assert "paginate: true" in front_matter
    assert "Phase 0 · Synthetic demonstration · Not for operational control." in front_matter


def test_deck_has_twenty_main_slides_and_six_backup_slides() -> None:
    _, slides = _front_matter_and_slides()
    assert len(slides) == MAIN_SLIDE_COUNT + BACKUP_SLIDE_COUNT
    assert all("backup" not in _classes(slide) for slide in slides[:MAIN_SLIDE_COUNT])
    assert all("backup" in _classes(slide) for slide in slides[MAIN_SLIDE_COUNT:])


def test_every_slide_carries_exactly_one_timed_speaker_note() -> None:
    _, slides = _front_matter_and_slides()
    for index, slide in enumerate(slides, start=1):
        notes = NOTE_PATTERN.findall(slide)
        assert len(notes) == 1, f"slide {index} must carry exactly one speaker note"
        _duration_seconds(notes[0])


def test_main_slides_fit_the_thirty_minute_budget() -> None:
    _, slides = _front_matter_and_slides()
    durations = [
        _duration_seconds(NOTE_PATTERN.findall(slide)[0]) for slide in slides[:MAIN_SLIDE_COUNT]
    ]
    total = sum(durations)
    assert MIN_TALK_SECONDS <= total <= MAX_TALK_SECONDS, (
        f"main slides speak for {total // 60}:{total % 60:02d}; the budget is 29:00-30:00"
    )
    assert all(duration > 0 for duration in durations)


def test_backup_slides_are_outside_the_speaking_budget() -> None:
    _, slides = _front_matter_and_slides()
    for slide in slides[MAIN_SLIDE_COUNT:]:
        assert _duration_seconds(NOTE_PATTERN.findall(slide)[0]) == 0


def test_referenced_images_are_provided_by_the_sync_script() -> None:
    sync_script = _read(PRESENTATION / "scripts" / "sync-images.mjs")
    available = set(re.findall(r'"([\w-]+\.png)"', sync_script))
    referenced = set(IMAGE_PATTERN.findall(_read(SLIDES)))
    assert referenced, "the deck should use at least one visual"
    assert referenced <= available, f"unknown images referenced: {sorted(referenced - available)}"


def test_every_css_class_used_by_the_deck_exists_in_the_theme() -> None:
    theme = _read(THEME)
    text = _read(SLIDES)
    used: set[str] = set()
    for value in HTML_CLASS_PATTERN.findall(text):
        used.update(value.split())
    for value in SCOPED_CLASS_PATTERN.findall(text):
        used.update(value.split())
    unknown = {name for name in used if f".{name}" not in theme}
    assert unknown == set(), f"classes missing from theme.css: {sorted(unknown)}"


def test_deck_carries_no_placeholder_text() -> None:
    text = _read(SLIDES)
    found = [marker for marker in PLACEHOLDERS if marker in text]
    assert found == [], f"placeholder text left in the deck: {found}"


def test_deck_drops_the_synthetic_realism_slide_and_guardrail() -> None:
    text = _read(SLIDES)
    assert "Synthetic Data & OT Realism" not in text
    assert "Synthetic-only Phase 0" not in text
    assert "NS-DEMO-*" not in text


def test_deck_carries_the_architecture_and_ai_flow_diagrams() -> None:
    _, slides = _front_matter_and_slides()
    diagrams = [slide for slide in slides if '<div class="flow">' in slide]
    assert len(diagrams) == 2, "the deck needs an architecture diagram and an AI detail diagram"
    titles = [re.search(r"(?m)^#\s+(.*)$", slide).group(1) for slide in diagrams]
    assert titles == ["Architecture at a Glance", "AI Architecture in Detail"]


def test_deck_sizes_the_run_cost_for_one_site() -> None:
    _, slides = _front_matter_and_slides()
    cost = [slide for slide in slides if "What It Costs to Run One Site" in slide]
    assert len(cost) == 1
    for tier in ("**Mini**", "**Medium**", "**Large**"):
        assert tier in cost[0], f"the cost slide must size the {tier} tier"


def test_build_scripts_produce_html_pdf_and_pptx() -> None:
    manifest = json.loads(_read(PRESENTATION / "package.json"))
    scripts = manifest["scripts"]
    for target in ("html", "pdf", "pdf-notes", "pptx", "verify", "build"):
        assert target in scripts
    assert "--pptx" in scripts["pptx"]
    assert "--pdf" in scripts["pdf"]
    assert "--pdf-notes" in scripts["pdf-notes"]
    assert "@marp-team/marp-cli" in manifest["dependencies"]


def test_presentation_workflow_builds_and_publishes_the_deck() -> None:
    workflow = _read(ROOT / ".github" / "workflows" / "presentation.yml")
    assert "npm run build" in workflow
    assert "tests/presentation" in workflow
    assert "NovaSteel-Oral-Defense.pptx" in workflow
    assert "NovaSteel-Oral-Defense.pdf" in workflow
