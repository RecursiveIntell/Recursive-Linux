#!/usr/bin/env python3
"""Classify source repositories for selective encrypted backup.

A repository is excluded from the first cloud snapshot only when it is clean,
all local non-remote refs are exactly represented on an accessible admitted
remote, submodules are clean, and ignored content is known-rebuildable.
Every error fails closed to BACKUP.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlsplit

PRUNE_DIRS = {".git", "node_modules", "target", ".venv", "venv", "__pycache__", ".cache", ".gradle", ".next"}
REBUILDABLE_COMPONENTS = {
    "node_modules", "target", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".tox", ".nox", ".pnpm-store", ".gradle",
}
REBUILDABLE_PREFIXES = ((".next", "cache"), (".pio", "build"))


@dataclass
class RepoResult:
    path: str
    disposition: str
    reasons: list[str]
    remote_host: str | None = None
    remote_name: str | None = None
    dirty_entries: int = 0
    unknown_ignored_entries: int = 0
    local_ref_count: int = 0
    remote_ref_count: int = 0


def run(repo: Path, args: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        timeout=timeout,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def discover_repos(roots: list[Path]) -> list[Path]:
    found: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for current, dirs, _files in os.walk(root):
            here = Path(current)
            if (here / ".git").exists():
                found.add(here.resolve())
            dirs[:] = [d for d in dirs if d != ".git" and (d not in PRUNE_DIRS or (here / d / ".git").exists())]
    return sorted(found)


def parse_host(url: str) -> str:
    # scp-like Git syntax: git@github.com:owner/repo.git
    match = re.match(r"^(?:[^@/]+@)?([^:/]+):.+$", url)
    if match and "://" not in url:
        return match.group(1).lower()
    parsed = urlsplit(url)
    if parsed.hostname:
        return parsed.hostname.lower()
    return "local"


def remote_candidates(repo: Path, allowed_hosts: set[str]) -> list[tuple[str, str]]:
    names = run(repo, ["remote"], timeout=10)
    if names.returncode:
        return []
    candidates: list[tuple[str, str]] = []
    for name in names.stdout.splitlines():
        result = run(repo, ["remote", "get-url", name], timeout=10)
        if result.returncode:
            continue
        host = parse_host(result.stdout.strip())
        if host in allowed_hosts:
            candidates.append((name, host))
    candidates.sort(key=lambda pair: (pair[0] != "origin", pair[0]))
    return candidates


def local_refs(repo: Path) -> list[tuple[str, str]]:
    result = run(repo, ["for-each-ref", "--format=%(refname)%09%(objectname)"])
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "for-each-ref failed")
    refs: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        if "\t" not in line:
            continue
        ref, oid = line.split("\t", 1)
        if ref.startswith("refs/remotes/") or ref.startswith("refs/bisect/"):
            continue
        refs.append((ref, oid))
    return refs


def is_rebuildable_ignored(rel: str) -> bool:
    parts = tuple(part for part in Path(rel).parts if part not in (".", ""))
    if any(part in REBUILDABLE_COMPONENTS for part in parts):
        return True
    return any(all(component in parts for component in prefix) for prefix in REBUILDABLE_PREFIXES)


def ignored_unknown(repo: Path) -> tuple[int, list[str]]:
    result = run(repo, ["ls-files", "-z", "--others", "--ignored", "--exclude-standard"], timeout=90)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "ignored-file scan failed")
    unknown: list[str] = []
    for rel in filter(None, result.stdout.split("\0")):
        if not is_rebuildable_ignored(rel):
            unknown.append(rel)
    return len(unknown), unknown[:10]


def classify(repo: Path, allowed_hosts: set[str], network_timeout: int) -> RepoResult:
    reasons: list[str] = []
    result = RepoResult(path=str(repo), disposition="backup", reasons=reasons)
    try:
        status = run(repo, ["status", "--porcelain=v1", "--untracked-files=all"], timeout=90)
        if status.returncode:
            reasons.append("status-error")
            return result
        result.dirty_entries = len(status.stdout.splitlines())
        if result.dirty_entries:
            reasons.append("dirty-or-untracked")

        submodules = run(repo, ["submodule", "status", "--recursive"], timeout=90)
        if submodules.returncode:
            reasons.append("submodule-status-error")
        elif any(line[:1] in {"-", "+", "U"} for line in submodules.stdout.splitlines()):
            reasons.append("submodule-not-clean")

        unknown_count, examples = ignored_unknown(repo)
        result.unknown_ignored_entries = unknown_count
        if unknown_count:
            reasons.append("unknown-ignored:" + ",".join(examples))

        candidates = remote_candidates(repo, allowed_hosts)
        if not candidates:
            reasons.append("no-admitted-remote")
            return result
        remote_name, host = candidates[0]
        result.remote_name = remote_name
        result.remote_host = host

        refs = local_refs(repo)
        result.local_ref_count = len(refs)
        remote = run(repo, ["ls-remote", remote_name], timeout=network_timeout)
        if remote.returncode:
            reasons.append("remote-unreachable")
            return result
        remote_oids = {line.split()[0] for line in remote.stdout.splitlines() if line.split()}
        result.remote_ref_count = len(remote.stdout.splitlines())
        if not remote_oids:
            reasons.append("remote-empty")
            return result

        absent = [ref for ref, oid in refs if oid not in remote_oids]
        if absent:
            reasons.append("local-refs-not-exactly-remote:" + ",".join(absent[:10]))

        head = run(repo, ["rev-parse", "HEAD"], timeout=10)
        if head.returncode or head.stdout.strip() not in remote_oids:
            reasons.append("head-not-exactly-remote")

        if not reasons:
            result.disposition = "github-covered"
        return result
    except subprocess.TimeoutExpired:
        reasons.append("timeout")
        return result
    except Exception as exc:  # fail closed; message contains no credentials
        reasons.append("error:" + type(exc).__name__)
        return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("roots", nargs="+", type=Path)
    parser.add_argument("--allow-host", action="append", default=["github.com"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--exclude-output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--network-timeout", type=int, default=30)
    args = parser.parse_args()

    roots = [path.expanduser().resolve() for path in args.roots]
    repos = discover_repos(roots)
    allowed = {host.lower() for host in args.allow_host}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        results = list(pool.map(lambda repo: classify(repo, allowed, args.network_timeout), repos))
    results.sort(key=lambda item: item.path)

    payload = {
        "schema_version": 1,
        "policy": "fail-closed-github-exact-ref-coverage",
        "roots": [str(path) for path in roots],
        "repository_count": len(results),
        "github_covered_count": sum(item.disposition == "github-covered" for item in results),
        "backup_count": sum(item.disposition == "backup" for item in results),
        "results": [asdict(item) for item in results],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    covered = [item.path for item in results if item.disposition == "github-covered"]
    args.exclude_output.parent.mkdir(parents=True, exist_ok=True)
    args.exclude_output.write_text("".join(f"{path}/**\n" for path in covered))
    print(json.dumps({key: payload[key] for key in ("repository_count", "github_covered_count", "backup_count")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
