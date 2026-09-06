#!/usr/bin/env python3
"""Assemble the non-secret Workbench rootfs overlay and digest manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def validated_output(path: Path) -> Path:
    output = path.resolve()
    if output == ROOT or ROOT not in output.parents:
        raise RuntimeError("output must be a child path inside the project")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "build/rootfs")
    parser.add_argument("--manifest", type=Path, default=ROOT / "build/overlay-manifest.json")
    args = parser.parse_args()
    output = validated_output(args.output)
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(ROOT / "overlays", output)

    libexec = output / "usr/libexec/hermes-workbench"
    libexec.mkdir(parents=True, exist_ok=True)
    governor = libexec / "hermes_pressure_governor.py"
    shutil.copy2(ROOT / "scripts/hermes_pressure_governor.py", governor)
    governor.chmod(0o755)

    docs = output / "usr/share/doc/hermes-workbench-os"
    docs.mkdir(parents=True, exist_ok=True)
    for name in ("DESIGN-v0.2.md", "DECISIONS.md", "RECOVERY-RUNBOOK.md"):
        shutil.copy2(ROOT / "docs" / name, docs / name)

    records = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        records.append({
            "path": "/" + str(path.relative_to(output)),
            "bytes": path.stat().st_size,
            "mode": stat.S_IMODE(path.stat().st_mode),
            "sha256": sha256(path),
        })
    payload = {"schema_version": 1, "kind": "hwos-rootfs-overlay", "file_count": len(records), "files": records}
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"output": str(output), "file_count": len(records), "manifest": str(args.manifest)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
