from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).parents[1]


def load(name: str, relative: str):
    path = PROJECT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


media = load("media_preflight_test_module", "scripts/media_preflight.py")
assembler = load("assemble_payload_test_module", "scripts/assemble_payload.py")


class SafetyBoundaryTests(unittest.TestCase):
    def test_hardware_media_writer_is_quarantined(self) -> None:
        script = PROJECT / "scripts" / "create_bootable_usb.sh"
        source = script.read_text()
        for forbidden in ("dd if=", "USB_DEVICE", "hermes-workbench-vm.ks"):
            self.assertNotIn(forbidden, source)
        result = subprocess.run([str(script)], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertIn("BLOCKED", result.stdout)

    def test_btrfs_subvolume_suffix_is_removed(self) -> None:
        self.assertEqual(media.block_device_source("/dev/nvme0n1p3[/@]"), "/dev/nvme0n1p3")
        self.assertEqual(media.block_device_source("/dev/sda2"), "/dev/sda2")

    def test_assembly_accepts_project_child(self) -> None:
        expected = (PROJECT / "build/test-rootfs").resolve()
        self.assertEqual(assembler.validated_output(expected), expected)

    def test_assembly_rejects_project_root(self) -> None:
        with self.assertRaises(RuntimeError):
            assembler.validated_output(PROJECT)

    def test_assembly_rejects_outside_project(self) -> None:
        with self.assertRaises(RuntimeError):
            assembler.validated_output(Path("/tmp/hwos-outside"))


if __name__ == "__main__":
    unittest.main()
