#!/usr/bin/env python3
"""Validate the generated presentation package, text content, and placeholders."""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
import zipfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree


REQUIRED_PARTS = {"[Content_Types].xml", "ppt/presentation.xml"}
PLACEHOLDER = re.compile(r"\{\{[^{}]+\}\}|\b(?:TODO|TBD)\b|REPLACE_WITH", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    kind: str
    location: str
    detail: str


def local_name(tag: str) -> str:
    return tag.rsplit("}", maxsplit=1)[-1]


def target_part(relationship_part: str, target: str) -> str:
    relation_directory = PurePosixPath(relationship_part).parent
    source_directory = relation_directory.parent if relation_directory.name == "_rels" else relation_directory
    return posixpath.normpath(str(source_directory / target))


def slide_parts(names: set[str]) -> list[str]:
    return sorted(
        name
        for name in names
        if name.startswith("ppt/slides/") and name.endswith(".xml") and "/_rels/" not in name
    )


def validate(presentation: Path, minimum_slides: int) -> tuple[dict[str, object], list[Finding]]:
    findings: list[Finding] = []
    if not presentation.is_file():
        return {}, [Finding("missing-file", str(presentation), "Presentation file does not exist.")]
    if not zipfile.is_zipfile(presentation):
        return {}, [Finding("invalid-package", str(presentation), "File is not a ZIP-based PPTX package.")]

    with zipfile.ZipFile(presentation) as package:
        names = set(package.namelist())
        for required in REQUIRED_PARTS:
            if required not in names:
                findings.append(Finding("missing-part", required, "Required PPTX part is absent."))

        for relationship_part in sorted(name for name in names if name.endswith(".rels")):
            try:
                relationships = ElementTree.fromstring(package.read(relationship_part))
            except ElementTree.ParseError as error:
                findings.append(Finding("invalid-relationships", relationship_part, str(error)))
                continue
            for relationship in relationships:
                if relationship.attrib.get("TargetMode") == "External":
                    continue
                target = relationship.attrib.get("Target")
                if target and target_part(relationship_part, target) not in names:
                    findings.append(
                        Finding(
                            "broken-relationship",
                            relationship_part,
                            f"Target does not exist: {target}",
                        )
                    )

        slides = slide_parts(names)
        if len(slides) < minimum_slides:
            findings.append(
                Finding(
                    "slide-count",
                    "ppt/slides",
                    f"Expected at least {minimum_slides} slides; found {len(slides)}.",
                )
            )

        slide_text_counts: dict[str, int] = {}
        for slide in slides:
            try:
                document = ElementTree.fromstring(package.read(slide))
            except ElementTree.ParseError as error:
                findings.append(Finding("invalid-slide-xml", slide, str(error)))
                continue
            text_runs = [
                (node.text or "").strip()
                for node in document.iter()
                if local_name(node.tag) == "t" and (node.text or "").strip()
            ]
            slide_text_counts[slide] = len(text_runs)
            if not text_runs:
                findings.append(Finding("empty-slide", slide, "Slide has no readable text runs."))
            for text in text_runs:
                if PLACEHOLDER.search(text):
                    findings.append(Finding("placeholder", slide, text))

    report = {
        "presentation": str(presentation),
        "slideCount": len(slides),
        "slideTextCounts": slide_text_counts,
    }
    return report, findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--presentation",
        type=Path,
        default=Path("docs/presentation/archives/NovaSteel-Oral-Defense.pptx"),
        help="PPTX file to validate.",
    )
    parser.add_argument(
        "--minimum-slides",
        type=int,
        default=20,
        help="Minimum expected slide count.",
    )
    parser.add_argument("--json", dest="json_path", type=Path, help="Write a JSON report.")
    args = parser.parse_args()

    presentation = args.presentation.resolve()
    report, findings = validate(presentation, args.minimum_slides)
    report.update(
        {
            "status": "PASS" if not findings else "FAIL",
            "checkedAtUtc": datetime.now(UTC).isoformat(),
            "findings": [asdict(finding) for finding in findings],
        }
    )
    if args.json_path:
        output = args.json_path.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if findings:
        print("PPTX validation findings:", file=sys.stderr)
        for finding in findings:
            print(f"  [{finding.kind}] {finding.location}: {finding.detail}", file=sys.stderr)
        return 1

    print(
        f"PPTX package validation passed ({report['slideCount']} slides, "
        f"{sum(report['slideTextCounts'].values())} text runs)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
