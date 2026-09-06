from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WorkflowImageTests(unittest.TestCase):
    def test_wifi_watchdog_source_is_portable_and_never_unloads_driver(self) -> None:
        text = (ROOT / "scripts/wifi_watchdog.sh").read_text()
        self.assertIn("wifi-watchdog v5", text)
        self.assertIn("default_gateway", text)
        self.assertIn("WIFI_WATCHDOG_LIB_ONLY", text)
        self.assertNotIn("modprobe -r", text)
        self.assertNotIn("PurpleMama", text)
        self.assertNotIn("192.168.50.1", text)
        self.assertNotIn("/home/sikmindz", text)

    def test_wifi_watchdog_crash_filter_rejects_normal_driver_lines(self) -> None:
        script = ROOT / "scripts/wifi_watchdog.sh"
        probe = (
            f"WIFI_WATCHDOG_LIB_ONLY=1 source {script!s}; "
            "if kernel_line_is_crash 'rtw89_8852bte: loaded normally'; then exit 1; else exit 0; fi"
        )
        result = subprocess.run(["bash", "-c", probe], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_wifi_watchdog_crash_filter_accepts_ser_signature(self) -> None:
        script = ROOT / "scripts/wifi_watchdog.sh"
        probe = (
            f"WIFI_WATCHDOG_LIB_ONLY=1 source {script!s}; "
            "kernel_line_is_crash 'rtw89_8852bte: SER catches error: 0x1002'"
        )
        result = subprocess.run(["bash", "-c", probe], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_aspm_helper_is_topology_driven_and_preserves_other_link_bits(self) -> None:
        text = (ROOT / "scripts/rtw89_disable_aspm.sh").read_text()
        self.assertIn("CAP_EXP+10.w", text)
        self.assertIn("0xfffc", text.lower())
        self.assertIn("/sys/bus/pci/drivers/rtw89_8852bte", text)
        self.assertNotIn("00:02.2", text)
        self.assertNotIn("01:00.0", text)

    def test_aspm_helper_normalizes_sysfs_domain_bdf_for_setpci(self) -> None:
        script = ROOT / "scripts/rtw89_disable_aspm.sh"
        probe = (
            f"RTW89_ASPM_LIB_ONLY=1 source {script!s}; "
            "test \"$(setpci_bdf 0000:00:02.2)\" = '00:02.2'"
        )
        result = subprocess.run(["bash", "-c", probe], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_workflow_units_use_installed_paths_and_no_personal_home(self) -> None:
        expected = {
            "overlays/usr/lib/systemd/user/wifi-watchdog.service": "/usr/libexec/hermes-workbench/wifi-watchdog.sh",
            "overlays/usr/lib/systemd/user/disk-governor.service": "/usr/libexec/hermes-workbench/disk-governor.sh",
            "overlays/usr/lib/systemd/user/system-health-monitor.service": "/usr/libexec/hermes-workbench/system-health-monitor.sh",
            "overlays/usr/lib/systemd/system/rtw89-disable-aspm.service": "/usr/libexec/hermes-workbench/rtw89-disable-aspm.sh",
        }
        for relative, executable in expected.items():
            text = (ROOT / relative).read_text()
            self.assertIn(executable, text, relative)
            self.assertNotIn("/home/sikmindz", text, relative)

    def test_measured_tlp_profile_and_rtw89_module_policy_are_in_overlay(self) -> None:
        tlp = (ROOT / "overlays/etc/tlp.d/99-hermes-workbench.conf").read_text()
        for line in (
            "CPU_SCALING_GOVERNOR_ON_AC=powersave",
            "CPU_SCALING_GOVERNOR_ON_BAT=powersave",
            "CPU_ENERGY_PERF_POLICY_ON_AC=balance_performance",
            "CPU_ENERGY_PERF_POLICY_ON_BAT=balance_performance",
            "CPU_BOOST_ON_AC=1",
            "CPU_BOOST_ON_BAT=1",
            "CPU_SCALING_MAX_FREQ_ON_AC=2900000",
            "CPU_SCALING_MAX_FREQ_ON_BAT=2900000",
        ):
            self.assertIn(line, tlp)
        module = (ROOT / "overlays/etc/modprobe.d/70-rtw89.conf").read_text()
        self.assertIn("disable_aspm_l1=y", module)
        self.assertIn("disable_aspm_l1ss=y", module)
        self.assertIn("disable_clkreq=y", module)
        self.assertIn("disable_ps_mode=y", module)

    def test_package_manifest_has_one_power_owner_and_script_dependencies(self) -> None:
        packages = {
            line.strip()
            for line in (ROOT / "manifests/host-packages.txt").read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        self.assertTrue({"tlp", "tlp-pd", "lm_sensors", "iputils", "pciutils", "util-linux"} <= packages)
        self.assertNotIn("tuned-ppd", packages)

    def test_kickstarts_exclude_competing_power_profiles_daemon(self) -> None:
        for relative in ("kickstart/hermes-workbench.ks.in", "kickstart/hermes-workbench-vm.ks"):
            text = (ROOT / relative).read_text()
            self.assertIn("-power-profiles-daemon", text, relative)
            self.assertNotIn("tuned-ppd", text, relative)

    def test_both_kickstarts_have_exactly_one_overlay_install_marker(self) -> None:
        marker = "# @HWOS_INSTALL_OVERLAY@"
        for relative in ("kickstart/hermes-workbench.ks.in", "kickstart/hermes-workbench-vm.ks"):
            self.assertEqual((ROOT / relative).read_text().count(marker), 1, relative)

    def test_assembler_emits_all_workflow_payload_files(self) -> None:
        output = ROOT / "build/test-workflow-rootfs"
        manifest = ROOT / "build/test-workflow-overlay-manifest.json"
        shutil.rmtree(output, ignore_errors=True)
        manifest.unlink(missing_ok=True)
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts/assemble_payload.py"),
                    "--output",
                    str(output),
                    "--manifest",
                    str(manifest),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(manifest.read_text())
            indexed = {row["path"]: row for row in payload["files"]}
            expected = {
                "/usr/libexec/hermes-workbench/wifi-watchdog.sh",
                "/usr/libexec/hermes-workbench/rtw89-disable-aspm.sh",
                "/usr/libexec/hermes-workbench/disk-governor.sh",
                "/usr/libexec/hermes-workbench/system-health-monitor.sh",
                "/usr/lib/systemd/user/wifi-watchdog.service",
                "/usr/lib/systemd/system/rtw89-disable-aspm.service",
                "/etc/tlp.d/99-hermes-workbench.conf",
                "/etc/modprobe.d/70-rtw89.conf",
            }
            self.assertTrue(expected <= indexed.keys(), sorted(expected - indexed.keys()))
            for executable in (
                "/usr/libexec/hermes-workbench/wifi-watchdog.sh",
                "/usr/libexec/hermes-workbench/rtw89-disable-aspm.sh",
                "/usr/libexec/hermes-workbench/disk-governor.sh",
                "/usr/libexec/hermes-workbench/system-health-monitor.sh",
            ):
                self.assertEqual(indexed[executable]["mode"], 0o755)
        finally:
            shutil.rmtree(output, ignore_errors=True)
            manifest.unlink(missing_ok=True)

    def test_mkksiso_command_uses_loop_free_efi_path(self) -> None:
        path = ROOT / "scripts/build_installer_iso.py"
        spec = importlib.util.spec_from_file_location("build_installer_iso_command", path)
        if spec is None or spec.loader is None:
            self.fail(f"could not load {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        command = module.mkksiso_container_command(
            prepared=type("Prepared", (), {
                "rendered_kickstart": ROOT / "build/a.ks",
                "payload_archive": ROOT / "build/payload.tar.gz",
            })(),
            input_iso=Path("/tmp/input.iso"),
            output_iso=ROOT / "build/output.iso",
        )
        self.assertIn("--skip-mkefiboot", command[-1])

    def test_installer_builder_prepares_payload_and_rendered_kickstart(self) -> None:
        path = ROOT / "scripts/build_installer_iso.py"
        spec = importlib.util.spec_from_file_location("build_installer_iso", path)
        if spec is None or spec.loader is None:
            self.fail(f"could not load {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        result = module.prepare_installer(
            kickstart=ROOT / "kickstart/hermes-workbench-vm.ks",
            build_dir=ROOT / "build/test-installer-prep",
        )
        try:
            self.assertTrue(result.payload_archive.is_file())
            self.assertTrue(result.rendered_kickstart.is_file())
            rendered = result.rendered_kickstart.read_text()
            self.assertNotIn("# @HWOS_INSTALL_OVERLAY@", rendered)
            self.assertIn("hwos-rootfs.tar.gz", rendered)
            self.assertIn("tar -xzf", rendered)
            self.assertIn("systemctl --root=/mnt/sysimage enable rtw89-disable-aspm.service", rendered)
            self.assertIn("systemctl --root=/mnt/sysimage --global enable wifi-watchdog.service", rendered)
        finally:
            shutil.rmtree(ROOT / "build/test-installer-prep", ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
