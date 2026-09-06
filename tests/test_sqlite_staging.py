from __future__ import annotations

import importlib.util
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "stage_sqlite_backups.py"
spec = importlib.util.spec_from_file_location("sqlite_stager", MODULE_PATH)
assert spec and spec.loader
stager = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = stager
spec.loader.exec_module(stager)


class SQLiteStagerTests(unittest.TestCase):
    def test_online_backup_contains_uncheckpointed_wal_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "live.db"
            destination = root / "staged" / "live.db"
            connection = sqlite3.connect(source)
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("CREATE TABLE facts(id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
            connection.execute("INSERT INTO facts(value) VALUES ('durable fixture')")
            connection.commit()
            self.assertTrue(Path(str(source) + "-wal").exists())

            receipt = stager.backup_one(source, destination)
            restored = sqlite3.connect(destination)
            try:
                rows = restored.execute("SELECT value FROM facts").fetchall()
            finally:
                restored.close()
                connection.close()

            self.assertEqual(rows, [("durable fixture",)])
            self.assertEqual(receipt["integrity"], "ok")
            self.assertEqual(receipt["table_count"], 1)
            self.assertEqual(len(receipt["sha256"]), 64)

    def test_busy_database_backup_has_a_total_deadline(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "busy.db"
            destination = root / "staged" / "busy.db"
            owner = sqlite3.connect(source)
            owner.execute("CREATE TABLE facts(id INTEGER PRIMARY KEY)")
            owner.commit()
            owner.execute("BEGIN EXCLUSIVE")
            try:
                started = time.monotonic()
                with self.assertRaisesRegex(TimeoutError, "backup deadline exceeded"):
                    stager.backup_one(source, destination, max_seconds=0.05)
                self.assertLess(time.monotonic() - started, 1.0)
            finally:
                owner.rollback()
                owner.close()
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
