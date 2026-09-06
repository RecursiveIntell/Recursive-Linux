from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "classify_github_coverage.py"
spec = importlib.util.spec_from_file_location("coverage_classifier", MODULE_PATH)
assert spec and spec.loader
classifier = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = classifier
spec.loader.exec_module(classifier)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)
    return result.stdout.strip()


class CoverageClassifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.remote = root / "remote.git"
        self.repo = root / "repo"
        subprocess.run(["git", "init", "--bare", str(self.remote)], check=True, capture_output=True)
        subprocess.run(["git", "init", str(self.repo)], check=True, capture_output=True)
        git(self.repo, "config", "user.name", "HWOS Test")
        git(self.repo, "config", "user.email", "hwos-test@example.invalid")
        (self.repo / "README.md").write_text("fixture\n")
        git(self.repo, "add", "README.md")
        git(self.repo, "commit", "-m", "fixture")
        git(self.repo, "remote", "add", "origin", str(self.remote))
        git(self.repo, "push", "-u", "origin", "HEAD:main")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def classify(self):
        return classifier.classify(self.repo, {"local"}, 10)

    def test_clean_exact_remote_is_covered(self) -> None:
        result = self.classify()
        self.assertEqual(result.disposition, "github-covered", result.reasons)

    def test_dirty_worktree_is_backed_up(self) -> None:
        (self.repo / "README.md").write_text("changed\n")
        result = self.classify()
        self.assertEqual(result.disposition, "backup")
        self.assertIn("dirty-or-untracked", result.reasons)

    def test_unpushed_commit_is_backed_up(self) -> None:
        (self.repo / "README.md").write_text("local commit\n")
        git(self.repo, "add", "README.md")
        git(self.repo, "commit", "-m", "local only")
        result = self.classify()
        self.assertEqual(result.disposition, "backup")
        self.assertTrue(any(reason.startswith("local-refs-not-exactly-remote") for reason in result.reasons))

    def test_unknown_ignored_artifact_is_backed_up(self) -> None:
        (self.repo / ".gitignore").write_text("artifact.bin\n")
        git(self.repo, "add", ".gitignore")
        git(self.repo, "commit", "-m", "ignore artifact")
        git(self.repo, "push", "origin", "HEAD:main")
        (self.repo / "artifact.bin").write_bytes(b"valuable local result")
        result = self.classify()
        self.assertEqual(result.disposition, "backup")
        self.assertTrue(any(reason.startswith("unknown-ignored") for reason in result.reasons))

    def test_known_rebuildable_ignored_target_is_covered(self) -> None:
        (self.repo / ".gitignore").write_text("target/\n")
        git(self.repo, "add", ".gitignore")
        git(self.repo, "commit", "-m", "ignore target")
        git(self.repo, "push", "origin", "HEAD:main")
        (self.repo / "target").mkdir()
        (self.repo / "target" / "object.o").write_bytes(b"rebuildable")
        result = self.classify()
        self.assertEqual(result.disposition, "github-covered", result.reasons)


if __name__ == "__main__":
    unittest.main()
