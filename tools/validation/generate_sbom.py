#!/usr/bin/env python3
"""Generate a lightweight CycloneDX SBOM from the repository's locked manifests."""

from __future__ import annotations

import argparse
import json
import re
import tomllib
import uuid
import xml.etree.ElementTree as element_tree
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote


REQUIREMENT_PATTERN = re.compile(
    r"^\s*([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?\s*==\s*([^\s;#]+)"
)
PACKAGE_REFERENCE_TAG = "PackageReference"


@dataclass(frozen=True, order=True)
class Component:
    ecosystem: str
    name: str
    version: str
    source: str

    @property
    def purl(self) -> str:
        encoded_name = quote(self.name, safe="/@")
        return f"pkg:{self.ecosystem}/{encoded_name}@{quote(self.version, safe='')}"

    def to_cyclonedx(self) -> dict[str, object]:
        component_type = "library" if self.name != "novasteel" else "application"
        return {
            "type": component_type,
            "name": self.name,
            "version": self.version,
            "purl": self.purl,
            "properties": [{"name": "novasteel:source", "value": self.source}],
        }


def parse_npm_locks(root: Path) -> list[Component]:
    components: list[Component] = []
    for lock_path in sorted(root.rglob("package-lock.json")):
        if any(part in {"node_modules", "artifacts"} for part in lock_path.parts):
            continue
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        relative_path = lock_path.relative_to(root).as_posix()
        root_package = lock.get("packages", {}).get("", {})
        if root_package.get("name") and root_package.get("version"):
            components.append(
                Component("npm", root_package["name"], root_package["version"], relative_path)
            )
        for install_path, package in lock.get("packages", {}).items():
            if not install_path.startswith("node_modules/"):
                continue
            name = install_path.rsplit("node_modules/", maxsplit=1)[-1]
            version = package.get("version")
            if name and version:
                components.append(Component("npm", name, str(version), relative_path))
    return components


def parse_python_requirements(root: Path) -> list[Component]:
    components: list[Component] = []
    for requirements_path in sorted(root.rglob("requirements*.txt")):
        if any(part in {"node_modules", ".venv", "artifacts"} for part in requirements_path.parts):
            continue
        relative_path = requirements_path.relative_to(root).as_posix()
        for line in requirements_path.read_text(encoding="utf-8").splitlines():
            match = REQUIREMENT_PATTERN.match(line)
            if match:
                components.append(
                    Component("pypi", match.group(1), match.group(2), relative_path)
                )
    return components


def parse_pyprojects(root: Path) -> list[Component]:
    components: list[Component] = []
    for project_path in sorted(root.rglob("pyproject.toml")):
        if any(part in {"node_modules", ".venv", "artifacts"} for part in project_path.parts):
            continue
        data = tomllib.loads(project_path.read_text(encoding="utf-8"))
        project = data.get("project", {})
        name = project.get("name")
        version = project.get("version")
        relative_path = project_path.relative_to(root).as_posix()
        if name and version:
            components.append(Component("pypi", str(name), str(version), relative_path))
    return components


def parse_nuget_projects(root: Path) -> list[Component]:
    components: list[Component] = []
    for project_path in sorted(root.rglob("*.csproj")):
        if any(part in {"bin", "obj", "artifacts"} for part in project_path.parts):
            continue
        relative_path = project_path.relative_to(root).as_posix()
        tree = element_tree.parse(project_path)
        for package in tree.iter():
            if package.tag.rsplit("}", maxsplit=1)[-1] != PACKAGE_REFERENCE_TAG:
                continue
            name = package.attrib.get("Include") or package.attrib.get("Update")
            version = package.attrib.get("Version")
            if not version:
                version_element = next(
                    (
                        child
                        for child in package
                        if child.tag.rsplit("}", maxsplit=1)[-1] == "Version"
                    ),
                    None,
                )
                version = version_element.text if version_element is not None else None
            if name and version:
                components.append(Component("nuget", name, version, relative_path))
    return components


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root.",
    )
    parser.add_argument("--output", type=Path, required=True, help="CycloneDX JSON output path.")
    args = parser.parse_args()

    root = args.root.resolve()
    components = {
        (component.ecosystem, component.name.lower(), component.version): component
        for component in (
            parse_npm_locks(root)
            + parse_python_requirements(root)
            + parse_pyprojects(root)
            + parse_nuget_projects(root)
        )
    }
    ordered_components = sorted(components.values())
    document = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(UTC).isoformat(),
            "tools": [{"vendor": "NovaSteel", "name": "generate_sbom.py"}],
            "component": {
                "type": "application",
                "name": "novasteel",
                "version": "0.1.0",
            },
        },
        "components": [component.to_cyclonedx() for component in ordered_components],
    }

    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(f"Generated SBOM with {len(ordered_components)} components: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
