#!/usr/bin/env python3
"""Run repository-local supply-chain and workflow hardening checks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


SKIPPED_DIRECTORIES = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "artifacts",
    "bin",
    "node_modules",
    "obj",
}
SOURCE_SUFFIXES = {
    ".bicep",
    ".bicepparam",
    ".cs",
    ".csproj",
    ".fs",
    ".fsproj",
    ".json",
    ".js",
    ".mjs",
    ".ps1",
    ".psm1",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".xml",
    ".yaml",
    ".yml",
}
PINNED_SHA = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
WORKFLOW_USE = re.compile(r"^\s*uses:\s*([^@\s]+)@([^\s#]+)", re.MULTILINE)
REQUIREMENT = re.compile(r"^\s*[A-Za-z0-9_.-]+(?:\[[^\]]+\])?\s*==\s*[^\s;#]+")


@dataclass(frozen=True)
class Finding:
    kind: str
    file: str
    detail: str


def relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part.lower() in SKIPPED_DIRECTORIES for part in path.relative_to(root).parts):
            continue
        if path.suffix.lower() in SOURCE_SUFFIXES or path.name.lower() in {".npmrc", "pip.conf"}:
            yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""


def non_comment_lines(text: str) -> str:
    return "\n".join(
        line
        for line in text.splitlines()
        if not line.lstrip().startswith(("#", ";", "//", "*"))
    )


def check_feed_configuration(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    protected_python = "https://packagefeedproxy.microsoft.io/pypi/simple"
    protected_nuget = "https://packagefeedproxy.microsoft.io/nuget/v3/index.json"

    pip_config = root / "pip.conf"
    pip_content = non_comment_lines(read_text(pip_config))
    if protected_python not in pip_content:
        findings.append(
            Finding("protected-python-feed", "pip.conf", "The approved Python index is missing.")
        )
    if "extra-index-url" in pip_content.lower():
        findings.append(
            Finding(
                "protected-python-feed",
                "pip.conf",
                "An extra Python index can bypass the protected feed.",
            )
        )

    nuget_config = root / "NuGet.Config"
    nuget_content = non_comment_lines(read_text(nuget_config))
    if "<clear" not in nuget_content or protected_nuget not in nuget_content:
        findings.append(
            Finding(
                "protected-nuget-feed",
                "NuGet.Config",
                "NuGet must clear inherited sources and use the approved feed.",
            )
        )
    return findings


def check_requirement_pins(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for requirement_path in root.rglob("requirements*.txt"):
        if any(part in SKIPPED_DIRECTORIES for part in requirement_path.parts):
            continue
        for number, line in enumerate(read_text(requirement_path).splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if not REQUIREMENT.match(stripped):
                findings.append(
                    Finding(
                        "unlocked-python-requirement",
                        relative(root, requirement_path),
                        f"line {number} is not an exact package pin: {stripped}",
                    )
                )
    return findings


def check_workflows(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    azure_login = "azure" + "/login@"
    static_credential_tokens = (
        "AZURE" + "_CREDENTIALS",
        "AZURE" + "_CLIENT_SECRET",
        "client" + "-secret:",
        "cred" + "s:",
    )

    workflow_root = root / ".github" / "workflows"
    if not workflow_root.is_dir():
        return [Finding("workflow-directory", ".github/workflows", "Workflow directory is missing.")]

    for workflow in sorted((*workflow_root.glob("*.yml"), *workflow_root.glob("*.yaml"))):
        content = non_comment_lines(read_text(workflow))
        workflow_name = relative(root, workflow)
        for action, revision in WORKFLOW_USE.findall(content):
            if action.startswith("docker://"):
                continue
            if not PINNED_SHA.fullmatch(revision):
                findings.append(
                    Finding(
                        "unpinned-action",
                        workflow_name,
                        f"{action}@{revision} is not pinned to a full commit SHA.",
                    )
                )
        if azure_login in content:
            if not re.search(r"(?m)^\s*id-token:\s*write\s*$", content):
                findings.append(
                    Finding(
                        "azure-oidc",
                        workflow_name,
                        "azure/login requires an id-token: write permission.",
                    )
                )
            for token in static_credential_tokens:
                if token.lower() in content.lower():
                    findings.append(
                        Finding(
                            "static-azure-credential",
                            workflow_name,
                            f"Forbidden credential-based Azure login token: {token}",
                        )
                    )
    return findings


def check_secret_literals(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    assignment = re.compile(
        r"""(?ix)
        (?:client[_-]?secret|password|api[_-]?key|access[_-]?key)
        \s*[:=]\s*
        ["'][A-Za-z0-9+/_=.-]{12,}["']
        """
    )
    private_key_marker = "-----BEGIN " + "PRIVATE" + " KEY-----"
    github_token_prefixes = ("gh" + "p_", "github" + "_pat_")

    for path in iter_files(root):
        if path.suffix.lower() in {".md", ".rst"}:
            continue
        content = non_comment_lines(read_text(path))
        if not content:
            continue
        file_name = relative(root, path)
        if assignment.search(content):
            findings.append(
                Finding(
                    "possible-static-secret",
                    file_name,
                    "A credential-like literal assignment was found.",
                )
            )
        if private_key_marker in content:
            findings.append(
                Finding("private-key", file_name, "A private key marker was found.")
            )
        if any(prefix in content.lower() for prefix in github_token_prefixes):
            findings.append(
                Finding("token-literal", file_name, "A GitHub token-shaped literal was found.")
            )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root.",
    )
    parser.add_argument("--json", dest="json_path", type=Path, help="Write a JSON report.")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        parser.error(f"Repository root does not exist: {root}")

    findings = (
        check_feed_configuration(root)
        + check_requirement_pins(root)
        + check_workflows(root)
        + check_secret_literals(root)
    )
    report = {
        "status": "PASS" if not findings else "FAIL",
        "checkedAtUtc": datetime.now(UTC).isoformat(),
        "findings": [asdict(finding) for finding in findings],
    }
    if args.json_path:
        output = args.json_path if args.json_path.is_absolute() else root / args.json_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if findings:
        print("Security gate findings:", file=sys.stderr)
        for finding in findings:
            print(f"  [{finding.kind}] {finding.file}: {finding.detail}", file=sys.stderr)
        return 1

    print("Repository-local security checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
