#!/usr/bin/env python3
"""Create transactionally consistent copies of live SQLite stores."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import stat
import sys
import time
from pathlib import Path
from typing import Any


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_database(path: Path) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=30)
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        user_version = connection.execute("PRAGMA user_version").fetchone()[0]
        page_count = connection.execute("PRAGMA page_count").fetchone()[0]
        page_size = connection.execute("PRAGMA page_size").fetchone()[0]
        tables = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        schema_rows = connection.execute(
            "SELECT type,name,tbl_name,coalesce(sql,'') FROM sqlite_schema ORDER BY type,name"
        ).fetchall()
        schema_digest = hashlib.sha256(json.dumps(schema_rows, separators=(",", ":")).encode()).hexdigest()
        return {
            "integrity": integrity,
            "user_version": user_version,
            "page_count": page_count,
            "page_size": page_size,
            "table_count": len(tables),
            "schema_sha256": schema_digest,
        }
    finally:
        connection.close()


def backup_one(source: Path, destination: Path, max_seconds: float = 120.0) -> dict[str, Any]:
    source = source.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(destination.parent, 0o700)
    partial = destination.with_suffix(destination.suffix + ".partial")
    partial.unlink(missing_ok=True)

    if max_seconds <= 0:
        raise ValueError("max_seconds must be positive")
    started = time.time()
    deadline = time.monotonic() + max_seconds

    def enforce_deadline(_status: int, _remaining: int, _total: int) -> None:
        if time.monotonic() >= deadline:
            raise TimeoutError(f"backup deadline exceeded after {max_seconds:g}s: {source}")

    sqlite_timeout = min(30.0, max_seconds)
    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True, timeout=sqlite_timeout)
    dst = sqlite3.connect(partial, timeout=sqlite_timeout)
    try:
        src.backup(dst, pages=4096, sleep=0.05, progress=enforce_deadline)
        dst.commit()
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    finally:
        dst.close()
        src.close()
    os.chmod(partial, stat.S_IRUSR | stat.S_IWUSR)
    partial.replace(destination)
    inspection = inspect_database(destination)
    if inspection["integrity"] != "ok":
        raise RuntimeError(f"integrity check failed for {source}: {inspection['integrity']}")
    return {
        "source": str(source),
        "destination": str(destination),
        "bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
        "elapsed_seconds": round(time.time() - started, 3),
        **inspection,
    }


def load_manifest(path: Path) -> list[Path]:
    sources: list[Path] = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            sources.append(Path(line).expanduser())
    return sources


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--per-db-timeout", type=float, default=120.0)
    args = parser.parse_args()
    staging = args.staging.expanduser().resolve()
    staging.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(staging, 0o700)

    records: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    home = Path.home().resolve()
    for source in load_manifest(args.manifest):
        try:
            relative = source.resolve().relative_to(home)
            destination = staging / relative
            print(f"backing up {relative}", flush=True)
            records.append(backup_one(source, destination, args.per_db_timeout))
        except Exception as exc:
            errors.append({"source": str(source), "error_type": type(exc).__name__, "error": str(exc)[:500]})

    receipt = {
        "schema_version": 1,
        "kind": "hwos-sqlite-online-backup",
        "created_at_unix": int(time.time()),
        "staging": str(staging),
        "all_passed": not errors and len(records) > 0,
        "database_count": len(records),
        "records": records,
        "errors": errors,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"all_passed": receipt["all_passed"], "database_count": len(records), "errors": len(errors)}))
    return 0 if receipt["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
