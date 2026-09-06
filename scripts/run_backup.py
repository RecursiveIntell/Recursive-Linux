#!/usr/bin/env python3
"""Prepare and execute an encrypted restic backup over an rclone Drive remote.

No password or OAuth token is accepted as a CLI argument. The repository
password must be supplied by RESTIC_PASSWORD_COMMAND, normally a secret-tool
lookup. Every network/storage error fails closed.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REMOTE = "gdrive"
DEFAULT_REPO_PATH = "HermesWorkbenchOS/restic"


def run(command: list[str], *, env: dict[str, str] | None = None, timeout: int = 3600, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=capture, env=env, timeout=timeout)


def require_programs() -> dict[str, str]:
    programs: dict[str, str] = {}
    for name in ("restic", "rclone", "git"):
        path = shutil.which(name)
        if not path:
            raise RuntimeError(f"required program missing: {name}")
        programs[name] = path
    return programs


def load_paths(manifest: Path) -> list[Path]:
    paths: list[Path] = []
    for raw in manifest.read_text().splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            candidate = Path(line).expanduser().resolve()
            if candidate.exists():
                paths.append(candidate)
    return paths


def restic_env(remote: str, repo_path: str) -> dict[str, str]:
    password_command = os.environ.get("RESTIC_PASSWORD_COMMAND")
    if not password_command:
        raise RuntimeError("RESTIC_PASSWORD_COMMAND is required; do not pass a password in argv")
    return {
        **os.environ,
        "RESTIC_REPOSITORY": f"rclone:{remote}:{repo_path}",
        "RESTIC_PASSWORD_COMMAND": password_command,
    }


def write_receipt(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def preflight(args: argparse.Namespace) -> int:
    programs = require_programs()
    remotes = run(["rclone", "listremotes"], timeout=30)
    remote_present = remotes.returncode == 0 and f"{args.remote}:" in remotes.stdout.splitlines()
    about_payload: dict[str, Any] | None = None
    about_error: str | None = None
    if remote_present:
        about = run(["rclone", "about", f"{args.remote}:", "--json"], timeout=90)
        if about.returncode == 0:
            try:
                about_payload = json.loads(about.stdout)
            except json.JSONDecodeError:
                about_error = "invalid-json"
        else:
            about_error = (about.stderr or about.stdout)[-1000:]
    payload = {
        "schema_version": 1,
        "kind": "hwos-google-drive-preflight",
        "created_at_unix": int(time.time()),
        "host": socket.gethostname(),
        "programs": {name: {"path": path} for name, path in programs.items()},
        "remote": args.remote,
        "remote_present": remote_present,
        "drive_about": about_payload,
        "drive_about_error": about_error,
        "source_count": len(load_paths(args.sources)),
        "ready_for_repository": remote_present and about_payload is not None,
    }
    write_receipt(args.receipt, payload)
    print(json.dumps({"remote_present": remote_present, "ready_for_repository": payload["ready_for_repository"], "drive_about": about_payload}, sort_keys=True))
    return 0 if payload["ready_for_repository"] else 2


def classify_sources(args: argparse.Namespace) -> None:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "classify_github_coverage.py"),
        str(Path.home() / "Coding"), str(Path.home() / "projects"), str(Path.home() / "Projects"),
        "--output", str(args.coverage_receipt),
        "--exclude-output", str(args.github_excludes),
        "--workers", str(args.workers),
        "--network-timeout", str(args.network_timeout),
    ]
    result = run(command, timeout=3600)
    if result.returncode:
        raise RuntimeError("GitHub coverage classifier failed: " + (result.stderr or result.stdout)[-1000:])


def require_sqlite_receipt(path: Path) -> None:
    payload = json.loads(path.read_text())
    if not payload.get("all_passed"):
        raise RuntimeError("SQLite online-backup receipt is missing or not passing")


def ensure_repo(env: dict[str, str], initialize: bool) -> None:
    snapshots = run(["restic", "snapshots", "--json"], env=env, timeout=180)
    if snapshots.returncode == 0:
        return
    combined = (snapshots.stderr or "") + snapshots.stdout
    if initialize and ("Is there a repository" in combined or "unable to open config file" in combined or "config file does not exist" in combined):
        created = run(["restic", "init"], env=env, timeout=300)
        if created.returncode:
            raise RuntimeError("restic init failed: " + (created.stderr or created.stdout)[-1000:])
        return
    raise RuntimeError("restic repository unavailable; use --init only for the admitted new Drive path")


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_exclude_patterns(manifests: list[Path]) -> list[str]:
    patterns: list[str] = []
    for manifest in manifests:
        for raw in manifest.read_text().splitlines():
            line = raw.strip()
            if line and not line.startswith("#"):
                patterns.append(os.path.expandvars(line))
    return patterns


def is_excluded(path: Path, patterns: list[str]) -> bool:
    value = str(path)
    return any(fnmatch.fnmatch(value, pattern) for pattern in patterns)


def create_sample_manifest(
    sources: list[Path],
    destination: Path,
    exclude_manifests: list[Path],
    sqlite_receipt: Path,
    limit: int = 24,
) -> None:
    patterns = load_exclude_patterns(exclude_manifests)
    candidates: list[tuple[str, Path]] = []
    sensitive_roots = {".ssh", ".gnupg", "keyrings", "Default", ".hermes"}
    sensitive_names = {".env", "cookies", "login data", "key4.db", "logins.json"}
    largest_personal: Path | None = None
    personal_roots = {"Documents", "Downloads", "Pictures", "Videos", "Desktop", "Music"}
    for source in sources:
        if source.name in sensitive_roots:
            continue
        if source.is_file() and source.stat().st_size <= 2 * 1024 * 1024:
            if not is_excluded(source, patterns):
                candidates.append((hashlib.sha256(str(source).encode()).hexdigest(), source))
            continue
        if not source.is_dir():
            continue
        for current, dirs, files in os.walk(source):
            current_path = Path(current)
            dirs[:] = [
                d for d in dirs
                if d not in {".git", "node_modules", "target", ".venv", "venv", "__pycache__"}
                and not is_excluded(current_path / d, patterns)
            ]
            for name in files:
                path = Path(current) / name
                if path.is_symlink() or name.lower() in sensitive_names or is_excluded(path, patterns):
                    continue
                try:
                    size = path.stat().st_size
                except OSError:
                    continue
                if 0 < size <= 2 * 1024 * 1024:
                    candidates.append((hashlib.sha256(str(path).encode()).hexdigest(), path))
                if source.name in personal_roots and size > 64 * 1024 * 1024:
                    if largest_personal is None or size > largest_personal.stat().st_size:
                        largest_personal = path
            if len(candidates) > limit * 40:
                break

    selected: list[tuple[str, Path]] = []
    seen: set[Path] = set()
    for _, path in sorted(candidates):
        if path not in seen:
            selected.append(("small", path))
            seen.add(path)
        if len(selected) == limit:
            break
    if largest_personal is not None:
        selected.append(("large-personal", largest_personal))

    sqlite_payload = json.loads(sqlite_receipt.read_text())
    sqlite_records = sqlite_payload.get("records", [])
    if sqlite_records:
        largest = max(sqlite_records, key=lambda record: int(record.get("bytes", 0)))
        semantic = next((record for record in sqlite_records if "semantic-memory.db" in record.get("source", "")), None)
        for role, record in (("sqlite-largest", largest), ("sqlite-semantic-memory", semantic)):
            if record:
                path = Path(record["destination"])
                if path.is_file() and all(path != existing for _, existing in selected):
                    selected.append((role, path))

    records = []
    for role, path in selected:
        records.append({"role": role, "path": str(path), "bytes": path.stat().st_size, "sha256": hash_file(path)})
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({"schema_version": 1, "samples": records}, indent=2) + "\n")


def backup(args: argparse.Namespace) -> int:
    require_programs()
    require_sqlite_receipt(args.sqlite_receipt)
    classify_sources(args)
    sources = load_paths(args.sources)
    if not sources:
        raise RuntimeError("no existing backup sources")
    create_sample_manifest(
        sources,
        args.sample_manifest,
        [args.common_excludes, args.live_excludes, args.github_excludes],
        args.sqlite_receipt,
    )
    env = restic_env(args.remote, args.repo_path)
    ensure_repo(env, args.init)
    command = [
        "restic", "backup", "--json", "--one-file-system", "--host", socket.gethostname(),
        "--tag", "hwos-pre-migration",
        "--exclude-file", str(args.common_excludes),
        "--exclude-file", str(args.live_excludes),
        "--exclude-file", str(args.github_excludes),
        *map(str, sources),
    ]
    started = time.time()
    result = run(command, env=env, timeout=args.timeout)
    payload: dict[str, Any] = {
        "schema_version": 1,
        "kind": "hwos-restic-backup",
        "created_at_unix": int(time.time()),
        "elapsed_seconds": round(time.time() - started, 3),
        "returncode": result.returncode,
        "source_count": len(sources),
        "repository": f"rclone:{args.remote}:{args.repo_path}",
    }
    for line in reversed(result.stdout.splitlines()):
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if parsed.get("message_type") == "summary":
            payload["summary"] = parsed
            break
    if result.returncode:
        payload["error_tail"] = (result.stderr or result.stdout)[-2000:]
    write_receipt(args.receipt, payload)
    print(json.dumps({"returncode": result.returncode, "summary": payload.get("summary")}, sort_keys=True))
    return result.returncode


def streamed_dump_digest(env: dict[str, str], snapshot_id: str, path: str, timeout: int) -> tuple[int, str | None, str]:
    with tempfile.TemporaryFile() as error_file:
        restic = subprocess.Popen(
            ["restic", "--no-cache", "dump", snapshot_id, path],
            env=env, stdout=subprocess.PIPE, stderr=error_file,
        )
        assert restic.stdout is not None
        hasher = subprocess.Popen(["sha256sum"], stdin=restic.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        restic.stdout.close()
        try:
            hash_output, _ = hasher.communicate(timeout=timeout)
            restic_rc = restic.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            restic.kill()
            hasher.kill()
            restic.wait()
            hasher.wait()
            return 124, None, "restore-sample-timeout"
        error_file.seek(0)
        error_tail = error_file.read().decode(errors="replace")[-1000:]
        digest = hash_output.decode().split()[0] if hasher.returncode == 0 and hash_output else None
        return restic_rc if restic_rc else hasher.returncode, digest, error_tail


def verify(args: argparse.Namespace) -> int:
    env = restic_env(args.remote, args.repo_path)
    check = run(["restic", "check", "--read-data-subset=5%"], env=env, timeout=args.timeout)
    backup_payload = json.loads(args.backup_receipt.read_text())
    snapshot_id = backup_payload.get("summary", {}).get("snapshot_id")
    if not snapshot_id:
        raise RuntimeError("passing backup receipt with snapshot_id is required")
    samples = json.loads(args.sample_manifest.read_text()).get("samples", [])
    sample_results = []
    for sample in samples:
        returncode, digest, error_tail = streamed_dump_digest(env, snapshot_id, sample["path"], min(args.timeout, 7200))
        sample_results.append({
            "role": sample.get("role"), "path": sample["path"], "returncode": returncode,
            "expected_sha256": sample["sha256"], "actual_sha256": digest,
            "passed": returncode == 0 and digest == sample["sha256"],
            "error_tail": error_tail if returncode else None,
        })
    payload = {
        "schema_version": 1,
        "kind": "hwos-restic-restore-verification",
        "created_at_unix": int(time.time()),
        "check_passed": check.returncode == 0,
        "sample_count": len(sample_results),
        "samples_passed": all(item["passed"] for item in sample_results) and bool(sample_results),
        "all_passed": check.returncode == 0 and all(item["passed"] for item in sample_results) and bool(sample_results),
        "sample_results": sample_results,
        "check_output_tail": (check.stdout + check.stderr)[-2000:],
    }
    write_receipt(args.receipt, payload)
    print(json.dumps({key: payload[key] for key in ("check_passed", "sample_count", "samples_passed", "all_passed")}, sort_keys=True))
    return 0 if payload["all_passed"] else 1


def parser() -> argparse.ArgumentParser:
    base = argparse.ArgumentParser()
    sub = base.add_subparsers(dest="command", required=True)
    for name in ("preflight", "backup", "verify"):
        item = sub.add_parser(name)
        item.add_argument("--remote", default=DEFAULT_REMOTE)
        item.add_argument("--repo-path", default=DEFAULT_REPO_PATH)
        item.add_argument("--receipt", type=Path, required=True)
        item.add_argument("--sources", type=Path, default=ROOT / "manifests" / "backup-sources.txt")
        item.add_argument("--timeout", type=int, default=24 * 3600)
        if name == "backup":
            item.add_argument("--init", action="store_true")
            item.add_argument("--common-excludes", type=Path, default=ROOT / "manifests" / "backup-excludes.txt")
            item.add_argument("--live-excludes", type=Path, default=ROOT / "manifests" / "backup-live-state-excludes.txt")
            item.add_argument("--github-excludes", type=Path, default=ROOT / "receipts" / "github-covered-excludes.txt")
            item.add_argument("--coverage-receipt", type=Path, default=ROOT / "receipts" / "github-coverage.json")
            item.add_argument("--sqlite-receipt", type=Path, default=ROOT / "receipts" / "sqlite-backup-receipt.json")
            item.add_argument("--sample-manifest", type=Path, default=ROOT / "receipts" / "restore-samples.json")
            item.add_argument("--workers", type=int, default=6)
            item.add_argument("--network-timeout", type=int, default=30)
        if name == "verify":
            item.add_argument("--sample-manifest", type=Path, default=ROOT / "receipts" / "restore-samples.json")
            item.add_argument("--backup-receipt", type=Path, default=ROOT / "receipts" / "restic-backup.json")
    return base


def main() -> int:
    args = parser().parse_args()
    try:
        return {"preflight": preflight, "backup": backup, "verify": verify}[args.command](args)
    except Exception as exc:
        payload = {"schema_version": 1, "kind": f"hwos-{args.command}-failure", "error_type": type(exc).__name__, "error": str(exc)[:2000]}
        write_receipt(args.receipt, payload)
        print(json.dumps(payload), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
