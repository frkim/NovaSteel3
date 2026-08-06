"""Structural validation for the Marp deck under ``docs/presentation/``.

The deck is generated in CI (``.github/workflows/presentation.yml``) straight from
``docs/presentation/slides.md``. These checks keep that source buildable and keep the
37-40 minute speaking budget honest before a single browser is started.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PRESENTATION = ROOT / "docs" / "presentation"
SLIDES = PRESENTATION / "slides.md"
THEME = PRESENTATION / "theme.css"

MAIN_SLIDE_COUNT = 38
BACKUP_SLIDE_COUNT = 17
MIN_TALK_SECONDS = 37 * 60
MAX_TALK_SECONDS = 40 * 60

NOTE_PATTERN = re.compile(r"<!--(?!\s*_)(.*?)-->", re.DOTALL)
TIMING_PATTERN = re.compile(r"^\s*⏱\s*(\d+):([0-5]\d)\s*·\s")
SCOPED_CLASS_PATTERN = re.compile(r"<!--\s*_class:\s*(.*?)\s*-->")
HTML_CLASS_PATTERN = re.compile(r'class="([^"]+)"')
IMAGE_PATTERN = re.compile(r"!\[[^\]]*\]\(images/([^)]+)\)")
HTML_IMAGE_PATTERN = re.compile(r'<img[^>]+src="images/([^"]+)"')
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
    assert "AI advises, humans decide" in front_matter
    assert "Phase 0" not in front_matter


def test_deck_never_mentions_a_phase_zero() -> None:
    """The "Phase 0" label was retired; the demonstration is named, not numbered."""

    assert "Phase 0" not in _read(SLIDES)


def test_deck_has_expected_main_and_backup_slides() -> None:
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


def test_main_slides_fit_the_thirty_eight_minute_budget() -> None:
    _, slides = _front_matter_and_slides()
    durations = [
        _duration_seconds(NOTE_PATTERN.findall(slide)[0]) for slide in slides[:MAIN_SLIDE_COUNT]
    ]
    total = sum(durations)
    assert MIN_TALK_SECONDS <= total <= MAX_TALK_SECONDS, (
        f"main slides speak for {total // 60}:{total % 60:02d}; the budget is 37:00-40:00"
    )
    assert all(duration > 0 for duration in durations)


def test_deck_carries_a_compliance_slide_instead_of_the_deployment_slide() -> None:
    """Regulatory posture earns a main slide; capacity and scale move to the appendix."""

    _, slides = _front_matter_and_slides()
    main = slides[:MAIN_SLIDE_COUNT]
    backup = slides[MAIN_SLIDE_COUNT:]

    compliance = [slide for slide in main if re.search(r"(?m)^#\s+Compliance\s*$", slide)]
    assert len(compliance) == 1
    for regulation in ("EU AI Act", "EU ETS", "IEC 62443", "NIS2", "GDPR"):
        assert regulation in compliance[0], f"the compliance slide must name {regulation}"

    assert not any("# Deployment, Capacity & Scale" in slide for slide in main)
    assert not any("Appendix — Deployment, Capacity & Scale" in slide for slide in backup)


def test_security_slide_names_the_agent_security_principles() -> None:
    _, slides = _front_matter_and_slides()
    security = [slide for slide in slides if "# Security, Identity & EU Data Residency" in slide]
    assert len(security) == 1
    for principle in (
        "Zero Trust",
        "Least Privilege",
        "Defense in Depth",
        "Security Left Shift",
        "Data Minimization",
    ):
        assert principle in security[0], f"the security slide must name {principle}"


def test_demo_handoff_contains_only_the_demo_sequence() -> None:
    _, slides = _front_matter_and_slides()
    handoff = [slide for slide in slides if "What You'll See Next" in slide]
    assert len(handoff) == 1
    for removed in (
        "Live, deterministic, synthetic",
        "Accelerated 60× clock",
        "Every screen labeled synthetic",
        "10-minute demonstration",
    ):
        assert removed not in handoff[0]
    assert "Fleet overview" in handoff[0]
    assert "Recap — targets vs. evidence" in handoff[0]


def test_backup_slides_are_outside_the_speaking_budget() -> None:
    _, slides = _front_matter_and_slides()
    for slide in slides[MAIN_SLIDE_COUNT:]:
        assert _duration_seconds(NOTE_PATTERN.findall(slide)[0]) == 0


def test_referenced_images_are_provided_by_the_sync_script() -> None:
    sync_script = _read(PRESENTATION / "scripts" / "sync-images.mjs")
    available = set(re.findall(r'"([\w-]+\.(?:png|webp))"', sync_script))
    slides = _read(SLIDES)
    referenced = set(IMAGE_PATTERN.findall(slides)) | set(HTML_IMAGE_PATTERN.findall(slides))
    assert referenced, "the deck should use at least one visual"
    assert referenced <= available, f"unknown images referenced: {sorted(referenced - available)}"


def test_title_slide_carries_the_brand_and_partner_marks() -> None:
    """The NovaSteel and AxelorMetal wordmarks share the title-slide plate, and the
    Microsoft mark sits in the bottom-right corner. Each one is removed at render time
    when its source asset is absent, so a logo the repository cannot ship never leaves
    a broken image behind."""

    _, slides = _front_matter_and_slides()
    title = slides[0]
    assert 'class="brandbar"' in title
    assert 'class="corners"' in title
    for logo in (
        "novasteel-logo.png",
        "axelormetal-wordmark.png",
        "microsoft-logo.png",
    ):
        assert f'src="images/{logo}"' in title
        assert 'onerror="this.remove()"' in title

    sync_script = _read(PRESENTATION / "scripts" / "sync-images.mjs")
    assert "NovaSteel Logo.png" in sync_script
    assert "microsoft_logo.png" in sync_script


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
    titles: list[str] = []
    for slide in slides:
        if '<div class="flow">' not in slide:
            continue
        heading = re.search(r"(?m)^#\s+(.*)$", slide)
        assert heading is not None, "a diagram slide is missing its title"
        titles.append(heading.group(1))
    assert {"High Level Architecture", "AI Architecture in Detail"} <= set(titles), (
        "the deck needs an architecture diagram and an AI detail diagram"
    )
    assert titles.index("High Level Architecture") < titles.index("AI Architecture in Detail")


def test_requested_slides_are_named_and_ordered() -> None:
    _, slides = _front_matter_and_slides()
    titles = [
        re.search(r"(?m)^#\s+(.*)$", slide).group(1)
        for slide in slides
        if re.search(r"(?m)^#\s+(.*)$", slide)
    ]

    assert titles[1] == "Agenda"
    assert titles.index("Transformation Objectives") + 1 == titles.index("Personas & Journey")
    assert titles.index("Personas & Journey") + 1 == titles.index(
        "An Agent for Every Role — Human Judgment at the Center"
    )
    assert titles.index("One Governed Platform") + 1 == titles.index(
        "What's In — and What's Out"
    )
    assert titles.index("What You'll See Next") < titles.index(
        "How We Built the Demo with an Agent Swarm"
    )
    assert titles.index(
        "NovaSteel vNext: Two-way Control with Microsoft Adaptive Cloud"
    ) + 1 == titles.index("Conclusion")
    assert titles.index("Next Steps") + 1 == titles.index("Thank You")
    assert titles[-1] == "Appendix — Fabric RTI"


def test_persona_and_employee_agent_story_are_present() -> None:
    _, slides = _front_matter_and_slides()
    personas = next(slide for slide in slides if "# Personas & Journey" in slide)
    assert "distinct knowledge and skills" in personas
    assert "historians, spreadsheets, MES exports and specialist software" in personas
    assert "Marc Weber" not in personas
    assert "Site Command Center" not in personas

    employee_agents = next(
        slide
        for slide in slides
        if "# An Agent for Every Role — Human Judgment at the Center" in slide
    )
    assert "images/employees-with-agents.png" in employee_agents
    assert "Accept · modify · reject" in employee_agents
    assert "No agent crosses into operational control" in employee_agents


def test_scope_boundary_and_deep_dives_are_explicit() -> None:
    _, slides = _front_matter_and_slides()

    scope = next(slide for slide in slides if "# What's In — and What's Out" in slide)
    for boundary in (
        "No PLC, interlock, furnace, recipe or production-setpoint control",
        "No autonomous schedule, work-order or CMMS commit",
        "no recommendation becomes authorization",
    ):
        assert boundary in scope

    expected = {
        "Deep Dive: Energy Dispatch Optimization": (
            "Shift production — do not reduce it",
            "constraints are never silently relaxed",
        ),
        "Deep Dive: Furnace Lining Remaining Useful Life": (
            "Physics-based RUL — not a black box",
            "delta method",
        ),
        "Deep Dive: In-line Quality Prediction": (
            "Detect drift before scrap occurs",
            "operationalWrite: false",
        ),
        "Deep Dive: GenAI Knowledge Capture": (
            "Capture expertise before it retires",
            "only **APPROVED** procedures become retrievable",
        ),
    }
    for title, phrases in expected.items():
        slide = next(slide for slide in slides if f"# {title}" in slide)
        assert "deep-dive" in _classes(slide)
        for phrase in phrases:
            assert phrase in slide


def test_fabric_diagrams_and_architecture_labels_are_present() -> None:
    text = _read(SLIDES)
    assert "# High Level Architecture" in text
    assert "Decision Center App" in text
    assert "Python FastAPI BFF" not in text
    assert "images/novasteel-architecture.png" in text
    assert "# NovaSteel Architecture" in text
    assert "images/fabric-rti-diagram.webp" in text
    assert "# Appendix — Why Fabric — and Why Not a Parallel Lake" not in text

    sync_script = _read(PRESENTATION / "scripts" / "sync-images.mjs")
    assert 'join(diagramDir, "NovaSteel Architecture.png")' in sync_script
    assert 'join(diagramDir, "fabric-rti-diagram.webp")' in sync_script
    assert "Fabric Architecture Diagram.png" not in sync_script
    assert "Fabric RTI Diagram.png" not in sync_script


def test_deck_sizes_the_run_cost_for_one_site() -> None:
    _, slides = _front_matter_and_slides()
    cost = [slide for slide in slides if "What It Costs to Run One Site" in slide]
    assert len(cost) == 1
    for tier in ("**Mini**", "**Medium**", "**Large**"):
        assert tier in cost[0], f"the cost slide must size the {tier} tier"
    for sku in ("F8", "F64", "F128"):
        assert sku in cost[0], f"the cost slide must name the {sku} deployment profile"
    assert "≈ €187k–€408k" in cost[0]
    assert "AI/ML train & score" not in cost[0]
    assert "same shared F-capacity pool" in cost[0]


def test_agent_swarm_slide_explains_the_agentic_development_stack() -> None:
    _, slides = _front_matter_and_slides()
    swarm = next(
        slide for slide in slides if "# How We Built the Demo with an Agent Swarm" in slide
    )
    for concept in (
        "GitHub Spec Kit",
        "Superpowers",
        "VS Code + Copilot CLI + GitHub Copilot app",
        "Specialized GitHub agents",
        "bounded branches and PRs",
    ):
        assert concept in swarm


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


def test_presentation_workflow_publishes_every_built_document_as_an_artifact() -> None:
    """The HTML deck, both PDFs and the PPTX must be downloadable from every run,
    including pull-request runs, so reviewers never have to build the deck."""

    workflow = _read(ROOT / ".github" / "workflows" / "presentation.yml")
    upload = workflow.split("- name: Publish the deck artifacts", 1)[1]
    upload = upload.split("- name: Assemble the Pages site", 1)[0]

    assert "actions/upload-artifact@" in upload
    for document in (
        "docs/presentation/dist/index.html",
        "docs/presentation/dist/NovaSteel-Oral-Defense.pdf",
        "docs/presentation/dist/NovaSteel-Oral-Defense-notes.pdf",
        "docs/presentation/dist/NovaSteel-Oral-Defense.pptx",
    ):
        assert document in upload
    assert "if-no-files-found: error" in upload
    assert "if:" not in upload, "deck artifacts must also be published on pull requests"


def test_presentation_workflow_publishes_the_deck_at_the_pages_root() -> None:
    """The Pages site root must serve the deck itself; publishing only under
    ``/deck/`` leaves https://<owner>.github.io/<repo>/ empty."""

    workflow = _read(ROOT / ".github" / "workflows" / "presentation.yml")
    assemble = workflow.split("- name: Assemble the Pages site", 1)[1]
    assemble = assemble.split("- name: Configure Pages", 1)[0]

    assert "-o ../../_site/index.html" in assemble
    assert "cp images/* ../../_site/images/" in assemble
    assert "dist/NovaSteel-Oral-Defense.pptx ../../_site/" in assemble
    assert "../../_site/.nojekyll" in assemble
    assert "../../_site/deck/index.html" in assemble, "keep the old /deck/ URL working"
    assert "path: _site" in workflow


def test_presentation_workflow_never_bootstraps_github_pages() -> None:
    """``enablement: true`` needs ``administration: write``, which GITHUB_TOKEN
    cannot have, so Pages must be enabled once in the repository settings and the
    publishing steps must not break the deck build when it is not."""

    workflow = _read(ROOT / ".github" / "workflows" / "presentation.yml")

    assert "enablement" not in workflow
    assert "actions/configure-pages@" in workflow
    assert "continue-on-error: true" in workflow
    assert "pages_configured: ${{ steps.pages.outcome }}" in workflow
    assert "steps.pages.outcome == 'success'" in workflow
    assert "needs.build.outputs.pages_configured == 'success'" in workflow
