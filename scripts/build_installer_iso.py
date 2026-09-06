#!/usr/bin/env python3
"""Prepare and build a bootable Workbench installer ISO without device writes."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "# @HWOS_INSTALL_OVERLAY@"
ARCHIVE_NAME = "hwos-rootfs.tar.gz"


@dataclass(frozen=True)
class PreparedInstaller:
    build_dir: Path
    rootfs: Path
    payload_archive: Path
    rendered_kickstart: Path
    overlay_manifest: Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def child_of_project(path: Path) -> Path:
    resolved = path.resolve()
    if resolved == ROOT or ROOT not in resolved.parents:
        raise ValueError(f"path must be below {ROOT}: {resolved}")
    return resolved


def deterministic_archive(rootfs: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for path in sorted(rootfs.rglob("*")):
                    relative = path.relative_to(rootfs)
                    info = archive.gettarinfo(str(path), arcname=str(relative))
                    info.uid = 0
                    info.gid = 0
                    info.uname = "root"
                    info.gname = "root"
                    info.mtime = 0
                    if info.isfile():
                        with path.open("rb") as handle:
                            archive.addfile(info, handle)
                    else:
                        archive.addfile(info)


def install_block() -> str:
    return r'''%post --nochroot --erroronfail --log=/mnt/sysimage/root/hwos-overlay-install.log
set -eu
payload=""
for candidate in \
    /run/install/repo/hwos-rootfs.tar.gz \
    /run/install/source/hwos-rootfs.tar.gz \
    /run/install/isodir/hwos-rootfs.tar.gz
do
    if [ -f "$candidate" ]; then payload="$candidate"; break; fi
done
if [ -z "$payload" ]; then
    echo "Hermes Workbench payload not found on installer media" >&2
    exit 1
fi
tar -xzf "$payload" -C /mnt/sysimage
systemctl --root=/mnt/sysimage enable rtw89-disable-aspm.service
systemctl --root=/mnt/sysimage enable tlp.service tlp-pd.service
systemctl --root=/mnt/sysimage --global enable wifi-watchdog.service
systemctl --root=/mnt/sysimage --global enable disk-governor.timer
systemctl --root=/mnt/sysimage --global enable system-health-monitor.service
if command -v restorecon >/dev/null 2>&1; then
    restorecon -RF /mnt/sysimage/etc /mnt/sysimage/usr || true
fi
%end'''


def prepare_installer(*, kickstart: Path, build_dir: Path) -> PreparedInstaller:
    kickstart = kickstart.resolve()
    if not kickstart.is_file() or ROOT not in kickstart.parents:
        raise ValueError("kickstart must be a source file inside the project")
    build_dir = child_of_project(build_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)
    rootfs = build_dir / "rootfs"
    manifest = build_dir / "overlay-manifest.json"
    subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / "scripts/assemble_payload.py"),
            "--output",
            str(rootfs),
            "--manifest",
            str(manifest),
        ],
        cwd=ROOT,
        check=True,
    )
    archive = build_dir / ARCHIVE_NAME
    deterministic_archive(rootfs, archive)
    source = kickstart.read_text()
    if source.count(MARKER) != 1:
        raise ValueError(f"expected exactly one {MARKER!r} in {kickstart}")
    rendered = build_dir / f"{kickstart.stem}.rendered.ks"
    rendered.write_text(source.replace(MARKER, install_block()))
    return PreparedInstaller(build_dir, rootfs, archive, rendered, manifest)


def mkksiso_container_command(
    *, prepared: PreparedInstaller, input_iso: Path, output_iso: Path
) -> list[str]:
    relative_ks = prepared.rendered_kickstart.relative_to(ROOT)
    relative_payload = prepared.payload_archive.relative_to(ROOT)
    relative_output = output_iso.relative_to(ROOT)
    return [
        "podman",
        "run",
        "--rm",
        "-v",
        f"{ROOT}:/work:rw",
        "-v",
        f"{input_iso.parent}:/input:ro",
        "registry.fedoraproject.org/fedora:44",
        "bash",
        "-lc",
        "dnf -qy install lorax >/dev/null && "
        f"mkksiso --skip-mkefiboot --ks /work/{relative_ks} "
        f"--add /work/{relative_payload} "
        f"/input/{input_iso.name} /work/{relative_output}",
    ]


def build_iso(*, prepared: PreparedInstaller, input_iso: Path, output_iso: Path, force: bool) -> dict[str, object]:
    input_iso = input_iso.resolve()
    output_iso = child_of_project(output_iso)
    if not input_iso.is_file():
        raise FileNotFoundError(input_iso)
    if output_iso.suffix.lower() != ".iso":
        raise ValueError("output must use .iso suffix")
    if output_iso.exists():
        if not force:
            raise FileExistsError(f"output exists; pass --force: {output_iso}")
        output_iso.unlink()
    output_iso.parent.mkdir(parents=True, exist_ok=True)

    command = mkksiso_container_command(
        prepared=prepared, input_iso=input_iso, output_iso=output_iso
    )
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode != 0:
        raise RuntimeError(f"mkksiso failed with exit code {completed.returncode}")
    return {
        "schema": "HermesWorkbenchInstallerBuildV1",
        "input_iso": str(input_iso),
        "input_sha256": sha256(input_iso),
        "kickstart": str(prepared.rendered_kickstart),
        "kickstart_sha256": sha256(prepared.rendered_kickstart),
        "payload": str(prepared.payload_archive),
        "payload_sha256": sha256(prepared.payload_archive),
        "output_iso": str(output_iso),
        "output_bytes": output_iso.stat().st_size,
        "output_sha256": sha256(output_iso),
        "physical_devices_written": [],
        "exit_code": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kickstart", type=Path, default=ROOT / "kickstart/hermes-workbench.ks.in")
    parser.add_argument("--build-dir", type=Path, default=ROOT / "build/installer-production")
    parser.add_argument("--input-iso", type=Path)
    parser.add_argument("--output-iso", type=Path, default=ROOT / "build/output/hermes-workbench-installer.iso")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    prepared = prepare_installer(kickstart=args.kickstart, build_dir=args.build_dir)
    if args.prepare_only:
        result = {
            "prepared": True,
            "kickstart": str(prepared.rendered_kickstart),
            "payload": str(prepared.payload_archive),
            "payload_sha256": sha256(prepared.payload_archive),
        }
    else:
        if args.input_iso is None:
            parser.error("--input-iso is required unless --prepare-only is used")
        result = build_iso(
            prepared=prepared,
            input_iso=args.input_iso,
            output_iso=args.output_iso,
            force=args.force,
        )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
