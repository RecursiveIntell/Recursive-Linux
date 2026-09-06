#!/usr/bin/env python3
"""Read-only block-device identity preflight. This tool never opens a device."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path


def lsblk() -> dict:
    fields = "NAME,PATH,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL,VENDOR,TRAN,RM,HOTPLUG,SERIAL,WWN"
    result = subprocess.run(["lsblk", "--json", "--bytes", "-e7", "-o", fields], text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def flatten(devices: list[dict]) -> list[dict]:
    result: list[dict] = []
    for device in devices:
        result.append(device)
        result.extend(flatten(device.get("children") or []))
    return result


def block_device_source(findmnt_source: str) -> str:
    """Remove findmnt's optional Btrfs subvolume suffix, e.g. /dev/nvme0n1p3[/@]."""
    return findmnt_source.split("[", 1)[0]


def root_parent() -> str:
    raw_source = subprocess.run(["findmnt", "-n", "-o", "SOURCE", "/"], text=True, capture_output=True, check=True).stdout.strip()
    source = block_device_source(raw_source)
    # For partitions, resolve to the whole disk.
    pkname = subprocess.run(["lsblk", "-n", "-d", "-o", "PKNAME", source], text=True, capture_output=True)
    if pkname.returncode == 0 and pkname.stdout.strip():
        parent_path = Path("/dev") / pkname.stdout.strip()
        if parent_path.exists():
            return str(parent_path)
    # Fallback: traverse via -s
    parents = subprocess.run(["lsblk", "-n", "-s", "-o", "PATH", source], text=True, capture_output=True, check=True).stdout.splitlines()
    return parents[-1].strip() if parents else source


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", help="whole-disk path such as /dev/sdb")
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    inventory = flatten(lsblk()["blockdevices"])
    root_disk = root_parent()
    selected = next((item for item in inventory if item.get("path") == args.device), None) if args.device else None
    candidates = [
        item for item in inventory
        if item.get("type") == "disk" and item.get("path") != root_disk
        and (item.get("tran") == "usb" or item.get("rm") or item.get("hotplug"))
    ]
    selected_payload = None
    safe_candidate = False
    if selected:
        serial_material = (selected.get("serial") or selected.get("wwn") or "missing").encode()
        selected_payload = {
            key: selected.get(key) for key in ("name", "path", "size", "type", "fstype", "mountpoints", "model", "vendor", "tran", "rm", "hotplug")
        }
        selected_payload["stable_id_sha256"] = hashlib.sha256(serial_material).hexdigest()
        selected_payload["is_root_disk"] = selected.get("path") == root_disk
        safe_candidate = selected.get("type") == "disk" and not selected_payload["is_root_disk"] and selected.get("tran") == "usb"
    payload = {
        "schema_version": 1,
        "kind": "hwos-read-only-media-preflight",
        "created_at_unix": int(time.time()),
        "root_disk": root_disk,
        "candidate_count": len(candidates),
        "candidates": [{key: item.get(key) for key in ("path", "size", "model", "vendor", "tran", "rm", "hotplug", "mountpoints")} for item in candidates],
        "selected": selected_payload,
        "safe_candidate": safe_candidate,
        "mutation_authorized": False,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"root_disk": root_disk, "candidate_count": len(candidates), "selected": selected_payload, "safe_candidate": safe_candidate}, sort_keys=True))
    return 0 if (not args.device or safe_candidate) else 2


if __name__ == "__main__":
    sys.exit(main())
