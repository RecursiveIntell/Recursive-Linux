#!/usr/bin/env python3
"""Fail-closed static validation for the Workbench source tree."""
from __future__ import annotations

import json
import py_compile
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def package_manifest() -> set[str]:
    return {
        line.strip()
        for line in (ROOT / "manifests/host-packages.txt").read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def kickstart_packages(text: str) -> set[str]:
    match = re.search(r"^%packages[^\n]*\n(.*?)^%end\s*$", text, re.MULTILINE | re.DOTALL)
    if not match:
        raise ValueError("Kickstart %packages block missing")
    return {
        line.strip()
        for line in match.group(1).splitlines()
        if line.strip() and not line.lstrip().startswith("#") and not line.strip().startswith("-")
    }


def main() -> int:
    failures: list[str] = []
    checks: list[str] = []
    kickstart_path = ROOT / "kickstart/hermes-workbench.ks.in"
    kickstart = kickstart_path.read_text()

    forbidden = {
        "clearpart": r"(?m)^\s*clearpart\b",
        "autopart": r"(?m)^\s*autopart\b",
        "ignoredisk": r"(?m)^\s*ignoredisk\b",
        "zerombr": r"(?m)^\s*zerombr\b",
        "embedded-passphrase": r"--passphrase(?:=|\s)",
        "root-password": r"(?m)^\s*rootpw\b",
    }
    for label, pattern in forbidden.items():
        if re.search(pattern, kickstart):
            failures.append(f"unsafe production Kickstart directive: {label}")
    checks.append("production-kickstart-has-no-disk-wipe-or-secret-directives")

    manifest = package_manifest()
    embedded = kickstart_packages(kickstart)
    if manifest != embedded:
        missing = sorted(manifest - embedded)
        extra = sorted(embedded - manifest)
        failures.append(f"package manifest mismatch missing={missing} extra={extra}")
    checks.append("package-manifest-matches-kickstart")

    for path in (ROOT / "manifests").glob("*.json"):
        try:
            json.loads(path.read_text())
        except Exception as exc:
            failures.append(f"invalid JSON {path.relative_to(ROOT)}: {type(exc).__name__}")
    checks.append("json-manifests-parse")

    for path in [*(ROOT / "scripts").glob("*.py"), *(ROOT / "tests").glob("*.py")]:
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            failures.append(f"Python compile failed {path.relative_to(ROOT)}: {exc}")
    checks.append("python-sources-compile")

    secret_patterns = [
        re.compile(r"(?i)(oauth|access|refresh)[_-]?token\s*[:=]\s*['\"][A-Za-z0-9._-]{16,}"),
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ]
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in {".git", "build", "receipts", "__pycache__"} for part in path.parts):
            continue
        try:
            text = path.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        if any(pattern.search(text) for pattern in secret_patterns):
            failures.append(f"possible embedded secret in {path.relative_to(ROOT)}")
    checks.append("no-obvious-embedded-secrets")

    expected = [
        ROOT / "AGENTS.md",
        ROOT / "docs/DESIGN-v0.2.md",
        ROOT / "docs/DECISIONS.md",
        ROOT / "scripts/run_backup.py",
        ROOT / "scripts/stage_sqlite_backups.py",
        ROOT / "scripts/classify_github_coverage.py",
        ROOT / "scripts/hermes_pressure_governor.py",
    ]
    absent = [str(path.relative_to(ROOT)) for path in expected if not path.is_file()]
    if absent:
        failures.append(f"required files missing: {absent}")
    checks.append("required-source-present")

    payload = {"checks": checks, "failures": failures, "passed": not failures}
    print(json.dumps(payload, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
