from __future__ import annotations

import importlib.util
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).parents[1]
MODULE_PATH = PROJECT / "scripts" / "run_backup.py"
SPEC = importlib.util.spec_from_file_location("run_backup_test_module", MODULE_PATH)
assert SPEC and SPEC.loader
backup = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = backup
SPEC.loader.exec_module(backup)


class BackupPipelineTests(unittest.TestCase):
    def test_exact_covered_repository_pattern_is_excluded(self) -> None:
        patterns = ["/home/example/Coding/covered/**"]
        self.assertTrue(backup.is_excluded(Path("/home/example/Coding/covered/file.rs"), patterns))
        self.assertFalse(backup.is_excluded(Path("/home/example/Coding/kept/file.rs"), patterns))

    def test_sample_manifest_respects_excludes_and_includes_staged_sqlite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "Documents"
            source.mkdir()
            kept = source / "kept.txt"
            kept.write_text("kept")
            excluded = source / "excluded.txt"
            excluded.write_text("excluded")
            sqlite = root / "staged.db"
            sqlite.write_bytes(b"sqlite-fixture")
            excludes = root / "excludes.txt"
            excludes.write_text(f"{excluded}\n")
            sqlite_receipt = root / "sqlite.json"
            sqlite_receipt.write_text(json.dumps({
                "all_passed": True,
                "records": [{"source": "/live/state.db", "destination": str(sqlite), "bytes": sqlite.stat().st_size}],
            }))
            output = root / "samples.json"
            backup.create_sample_manifest([source], output, [excludes], sqlite_receipt, limit=10)
            payload = json.loads(output.read_text())
            paths = {record["path"] for record in payload["samples"]}
            self.assertIn(str(kept), paths)
            self.assertIn(str(sqlite), paths)
            self.assertNotIn(str(excluded), paths)

    def test_streamed_dump_hashes_without_buffering_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bindir = Path(tmp)
            restic = bindir / "restic"
            restic.write_text("#!/bin/sh\nprintf fixture-payload\n")
            restic.chmod(restic.stat().st_mode | stat.S_IXUSR)
            env = {**os.environ, "PATH": f"{bindir}:{os.environ['PATH']}"}
            returncode, digest, error = backup.streamed_dump_digest(env, "snapshot", "/fixture", 10)
            self.assertEqual(returncode, 0)
            self.assertEqual(digest, backup.hashlib.sha256(b"fixture-payload").hexdigest())
            self.assertEqual(error, "")


if __name__ == "__main__":
    unittest.main()
