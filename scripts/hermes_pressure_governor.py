#!/usr/bin/env python3
"""PSI-based optional-workload shedder for Hermes Workbench OS.

Dry-run is the default. `--apply` is required to stop any systemd user unit.
The governor never restarts units automatically; recovery remains explicit.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Pressure:
    some_avg10: float
    full_avg10: float


def parse_psi(text: str) -> Pressure:
    rows: dict[str, dict[str, float]] = {}
    for line in text.splitlines():
        fields = line.split()
        if not fields:
            continue
        values: dict[str, float] = {}
        for field in fields[1:]:
            if "=" not in field:
                continue
            key, value = field.split("=", 1)
            try:
                values[key] = float(value)
            except ValueError:
                continue
        rows[fields[0]] = values
    if "some" not in rows or "full" not in rows:
        raise ValueError("memory PSI must contain some and full rows")
    return Pressure(rows["some"].get("avg10", 0.0), rows["full"].get("avg10", 0.0))


def overloaded(pressure: Pressure, some_threshold: float, full_threshold: float) -> bool:
    return pressure.some_avg10 >= some_threshold or pressure.full_avg10 >= full_threshold


def stop_units(systemctl: str, units: list[str], apply: bool) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for unit in units:
        if not apply:
            records.append({"unit": unit, "action": "would-stop", "returncode": None})
            continue
        result = subprocess.run([systemctl, "--user", "stop", unit], text=True, capture_output=True, timeout=30)
        records.append({
            "unit": unit,
            "action": "stop",
            "returncode": result.returncode,
            "error_tail": result.stderr[-300:] if result.returncode else "",
        })
    return records


def write_state(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--psi-path", type=Path, default=Path("/proc/pressure/memory"))
    parser.add_argument("--state", type=Path, default=Path("/tmp/hermes-pressure-governor/state.json"))
    parser.add_argument("--some-threshold", type=float, default=8.0)
    parser.add_argument("--full-threshold", type=float, default=2.0)
    parser.add_argument("--consecutive", type=int, default=3)
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--unit", action="append", default=[])
    parser.add_argument("--systemctl", default="systemctl")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    units = args.unit or ["hermes-experimental.target", "hermes-ml-research.target", "hermes-media.target"]
    consecutive = 0
    incident = 0
    while True:
        try:
            pressure = parse_psi(args.psi_path.read_text())
            is_overloaded = overloaded(pressure, args.some_threshold, args.full_threshold)
            consecutive = consecutive + 1 if is_overloaded else 0
            actions: list[dict[str, object]] = []
            if consecutive >= args.consecutive:
                incident += 1
                actions = stop_units(args.systemctl, units, args.apply)
                consecutive = 0
            payload: dict[str, object] = {
                "schema_version": 1,
                "mode": "apply" if args.apply else "dry-run",
                "timestamp_unix": int(time.time()),
                "incident": incident,
                "pressure": asdict(pressure),
                "thresholds": {"some_avg10": args.some_threshold, "full_avg10": args.full_threshold},
                "overloaded": is_overloaded,
                "consecutive": consecutive,
                "actions": actions,
            }
            write_state(args.state, payload)
            if args.once:
                print(json.dumps(payload, sort_keys=True))
                return 0
        except Exception as exc:
            payload = {"schema_version": 1, "timestamp_unix": int(time.time()), "error_type": type(exc).__name__, "error": str(exc)[:500]}
            write_state(args.state, payload)
            if args.once:
                print(json.dumps(payload, sort_keys=True), file=sys.stderr)
                return 1
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
