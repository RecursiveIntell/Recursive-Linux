from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "hermes_pressure_governor.py"
spec = importlib.util.spec_from_file_location("pressure_governor", MODULE_PATH)
assert spec and spec.loader
governor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = governor
spec.loader.exec_module(governor)


class PressureGovernorTests(unittest.TestCase):
    def test_parse_and_threshold(self) -> None:
        pressure = governor.parse_psi(
            "some avg10=9.50 avg60=3.0 avg300=1.0 total=10\n"
            "full avg10=0.20 avg60=0.1 avg300=0.0 total=1\n"
        )
        self.assertEqual(pressure.some_avg10, 9.5)
        self.assertTrue(governor.overloaded(pressure, 8.0, 2.0))

    def test_full_pressure_threshold(self) -> None:
        pressure = governor.parse_psi(
            "some avg10=1.00 avg60=1.0 avg300=1.0 total=10\n"
            "full avg10=2.10 avg60=0.1 avg300=0.0 total=1\n"
        )
        self.assertTrue(governor.overloaded(pressure, 8.0, 2.0))

    def test_dry_run_never_invokes_systemctl(self) -> None:
        records = governor.stop_units("/definitely/missing/systemctl", ["optional.target"], False)
        self.assertEqual(records[0]["action"], "would-stop")
        self.assertIsNone(records[0]["returncode"])

    def test_bad_psi_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            governor.parse_psi("some avg10=1.0\n")

    def test_atomic_state_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            governor.write_state(path, {"ok": True})
            self.assertIn('"ok": true', path.read_text())
            self.assertFalse(path.with_suffix(".json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
