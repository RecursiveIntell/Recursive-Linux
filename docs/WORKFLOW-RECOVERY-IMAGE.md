# Workflow Recovery Installer

## Purpose and current boundary

This project produces an **interactive hardware-target Fedora 44 installer candidate** for the HP Laptop 15-fc0xxx. It is intended to recreate the reviewable, source-tree-defined parts of the current workstation configuration while keeping the existing Nobara installation as the working system. It is not hardware-qualified or production-ready.

The generated ISO is not a clone of the current disk. It does not contain personal data, credentials, browser state, semantic-memory databases, or mutable Ares/Hermes runtime state. Those remain separate backup-and-restore concerns.

No repository script writes a USB device. Converting the ISO to physical media remains a later exact-device action.

## Current local candidate

```text
build/output/hermes-workbench-recovery-installer-20260906-v2.iso
SHA-256 6f2e1406db4a4d5970f489589d5f1d51549e25e00fb1a88d5d1bd7b4430221fc
Size    1,217,396,736 bytes
```

The current VM-only candidate installed using a direct installer-kernel boot with the ISO as Fedora stage2/Kickstart source. Its resulting disk passed qcow2 inspection and then booted separately under matching QEMU BIOS to a Fedora login prompt. Installed workflow files matched source hashes, all six specified system/global-user enablement links were present, and `power-profiles-daemon` was absent. The production-profile ISO reached its UEFI GRUB menu, but an installed UEFI disk layout and UEFI first boot remain unverified.

The recorded v2 ISO was assembled locally by replacing the Kickstart and hash-identical payload in the first Fedora-derived candidate after the external source drive disconnected. It was not a fresh end-to-end rebuild directly from the official Fedora input. A clean rebuild remains required for reproducibility evidence.

## Included workflow components

The installer payload contains:

- portable Wi-Fi watchdog v5 with bounded NetworkManager radio recovery;
- RTL8852BE-VT module parameters and a topology-driven PCIe ASPM boot mitigation;
- the previously selected Ryzen 7 7730U 2.9 GHz TLP midpoint used on AC and battery;
- TLP and `tlp-pd` as the single power-policy owner;
- report-only disk-space monitoring;
- a low-overhead system-health state projection;
- the existing pressure-governor source and Workbench systemd profile units.

The Wi-Fi watchdog never unloads the `rtw89` kernel module. A prior local incident was recorded as associating module-unload recovery with a kernel oops; the current watchdog therefore does not unload the module. It dynamically discovers the active Wi-Fi interface, connection, and default gateway and does not embed a personal SSID or password.

See `manifests/workflow-components.json` for the source-to-installed-path map and explicit exclusions.

## Build

From the repository root:

```bash
python3 -B scripts/validate_project.py
python3 -B -m unittest discover -s tests -v

python3 -B scripts/build_installer_iso.py \
  --kickstart kickstart/hermes-workbench.ks.in \
  --build-dir build/installer-production \
  --input-iso /path/to/Fedora-Everything-netinst-x86_64-44-1.7.iso \
  --output-iso build/output/hermes-workbench-recovery-installer.iso
```

The builder:

1. assembles a non-secret rootfs payload;
2. emits a content manifest;
3. creates a normalized payload archive intended to improve repeatability; no byte-identical ISO rebuild is claimed;
4. renders the interactive hardware-target Kickstart;
5. uses Fedora 44 `mkksiso` in an ephemeral container;
6. leaves all output below the ignored `build/` directory.

The hardware-target Kickstart does not preselect disk clearing, automatic partitioning, a target disk, root password, user password, or an encryption secret. Storage and identity remain interactive, but proceeding through the installer can still modify storage and boot state.

## VM-only fixture

`kickstart/hermes-workbench-vm.ks` is a destructive test fixture for a disposable virtual disk named `vda`. It contains a deliberately public test password and must never be used on hardware, a bridged network, or a persistent guest.

Build it with a separate output path:

```bash
python3 -B scripts/build_installer_iso.py \
  --kickstart kickstart/hermes-workbench-vm.ks \
  --build-dir build/installer-vm \
  --input-iso /path/to/Fedora-Everything-netinst-x86_64-44-1.7.iso \
  --output-iso build/output/hermes-workbench-vm-installer.iso
```

A VM result proves only the tested virtual installation path. It cannot prove the Realtek Wi-Fi card, suspend, audio, battery, display, USB, firmware, or internal-disk behavior.

## Post-install bootstrap boundary

The installer intentionally does not embed:

- Wi-Fi passwords or NetworkManager profiles;
- API/OAuth tokens, browser cookies, SSH/GPG private keys, or VPN identity;
- Ares/Hermes mutable profile state;
- semantic-memory or Mnemes stores and admission credentials;
- PAIR/Ollama model blobs;
- CPU-router tunnel credentials;
- personal or automation Chrome profiles.

Those components require their supported restore or bootstrap paths after installation. An ISO build or VM boot must not be described as a complete restoration of the current workstation workflow.

## Later physical-media step

When physical media is actually wanted:

1. identify the exact USB device by stable by-id path, model, and size;
2. verify that it is not the internal NVMe or a backup disk;
3. record the ISO SHA-256 and device identity;
4. obtain explicit approval for that exact device;
5. write with a standard image writer;
6. read back and hash the written image where practical;
7. boot-test it without installing.

Until that gate, the ISO remains a local candidate file and no physical-media claim is supported.
