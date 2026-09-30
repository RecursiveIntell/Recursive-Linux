# Recursive Linux — Hermes Workbench OS

<!-- Documentation/source/release-metadata review: 2026-09-30; artifact evidence remains dated 2026-09-06 -->

A **Fedora 44 workstation installer prototype** and recovery-oriented workflow profile for a laptop-centered Linux environment. It packages reviewable, non-secret workstation controls—Wi-Fi fault recovery, a targeted PCIe ASPM mitigation, TLP policy, disk-space reporting, health projection, and existing Hermes Workbench systemd profiles—while keeping storage, identity, encryption, and device selection interactive.

> **Status — local candidate, not a hardware-ready distribution.** A hardware-target ISO has been built and structurally checked, and a separate disposable VM fixture installed and booted under the recorded BIOS/QEMU validation path. No physical-media write, hardware installation, internal-disk migration, or UEFI-installed-system verification is claimed or authorized by this repository.

## What is here

| Surface | Status | Evidence boundary |
|---|---|---|
| Fedora 44 hardware-target Kickstart | Source-present and locally validated | It does not preselect disk clearing, automatic partitioning, a target disk, credentials, or an encryption secret; proceeding through the interactive installer can still modify storage and boot state. |
| ISO construction pipeline | Exercised locally for the first Fedora-derived candidate | The final v2 artifact was assembled by replacing the Kickstart and hash-matching payload in that candidate; no clean end-to-end rebuild from official input has been completed. It never writes a block device. |
| Hardware-target ISO candidate | Structurally verified | Static inspection found BIOS and UEFI El Torito entries, a boot-configuration reference to the embedded Kickstart, an embedded payload hash matching the locally assembled payload, and `checkisomd5` PASS. These checks do not prove firmware-path boot or installation. |
| Disposable VM fixture | VM-verified (BIOS path) | An isolated QEMU VM installed and booted to a Fedora login prompt; this does not verify a physical laptop or an installed UEFI system. |
| Wi-Fi watchdog v5 | Source-present; separately exercised on the prior Nobara host | Uses a bounded NetworkManager radio cycle and never unloads `rtw89`; it mitigates recovery and does not cure RTL8852BE-VT firmware faults. |
| Physical USB media or laptop installation | **Not verified / not authorized** | Requires an exact-device identity receipt and a separate operator approval. |

The public, sanitized evidence receipt is [`receipts/public/20260906-workflow-image-v2.json`](receipts/public/20260906-workflow-image-v2.json). It records the candidate ISO hash, validation scope, intentional exclusions, and limits of the evidence.

## Release artifact

The [v0.1.0-experimental pre-release](https://github.com/RecursiveIntell/Recursive-Linux/releases/tag/v0.1.0-experimental) was published on September 6, 2026 and includes the ISO below as an uploaded release asset. The release metadata reports the same byte length and SHA-256 shown here; this documentation review did not download or boot the ISO. The binary is not placed in Git history.

```text
File:    hermes-workbench-recovery-installer-20260906-v2.iso
Bytes:   1,217,396,736
SHA-256: 6f2e1406db4a4d5970f489589d5f1d51549e25e00fb1a88d5d1bd7b4430221fc
```

Verify a downloaded release asset before using it:

```bash
sha256sum hermes-workbench-recovery-installer-20260906-v2.iso
# expected: 6f2e1406db4a4d5970f489589d5f1d51549e25e00fb1a88d5d1bd7b4430221fc
```

A matching checksum proves only that the downloaded bytes match this recorded local candidate. It does **not** establish reproducibility, media-write correctness, or hardware safety.

## Quick start: inspect and validate the source

**Prerequisites:** Linux, Python 3, and a checkout of this repository. The source validation below does not write an installer image or modify disks.

```bash
git clone https://github.com/RecursiveIntell/Recursive-Linux.git
cd Recursive-Linux
python3 -B scripts/validate_project.py
python3 -B -m unittest discover -s tests -v
```

The expected success signals are a JSON result with `"passed": true` from `validate_project.py` and an all-passing `unittest` summary. These commands verify static project invariants and repository tests; they do not validate an ISO, a VM, or physical hardware.

## Build an installer candidate

The builder requires a local Fedora 44 netinstall ISO and Podman access to the Fedora container image. It writes only below this repository's ignored `build/` directory.

```bash
python3 -B scripts/build_installer_iso.py \
  --kickstart kickstart/hermes-workbench.ks.in \
  --build-dir build/installer-production \
  --input-iso /path/to/Fedora-Everything-netinst-x86_64-44-1.7.iso \
  --output-iso build/output/hermes-workbench-recovery-installer.iso
```

The hardware-target Kickstart does not preselect disk clearing, automatic partitioning, storage, encryption, identity, or the installation target. Installation remains interactive, but proceeding can still modify storage and boot state. Do not convert that boundary into an unattended hardware installation without an explicit device-bound design, validation, and approval.

For a disposable QEMU-only fixture, use `kickstart/hermes-workbench-vm.ks` and a separate output/build directory. That fixture deliberately wipes its virtual `vda` disk and contains a public test credential. It must never be used on hardware, bridged networking, or a persistent guest.

## Included workflow components

The installer payload maps reviewed source files to installed paths through [`manifests/workflow-components.json`](manifests/workflow-components.json):

- **Wi-Fi watchdog v5** — detects loss of connectivity and selected `rtw89` firmware-fault signals, discovers active connection context, and performs a bounded NetworkManager radio recovery. It never unloads the kernel module.
- **RTL8852BE-VT PCIe ASPM mitigation** — applies `pcie_aspm=off` and a topology-driven service that preserves non-ASPM PCIe link-control bits.
- **Measured TLP midpoint** — a 2.9 GHz AMD P-state midpoint used for the target laptop profile. It is not a universal hardware recommendation.
- **Report-only disk governor** — reports and notifies; it has no deletion or offload authority.
- **System-health projection** — writes rebuildable local state and does not repair or delete state.
- **Hermes Workbench profiles** — existing user systemd targets/slices and pressure-governor source remain governed by their existing source and tests.

## Deliberate exclusions

This project is **not** a disk clone or personal-environment backup. The ISO and public repository intentionally exclude:

- Wi-Fi credentials and NetworkManager connection profiles;
- API/OAuth tokens, browser cookies/passwords, SSH/GPG private keys, and VPN identity;
- mutable Ares/Hermes profile state, semantic-memory/Mnemes stores, and admission credentials;
- PAIR/Ollama model blobs, remote-compute credentials, and personal or automation browser profiles;
- block-device writers and autonomous hardware-install steps.

Restoring those materials, if desired, must use separate supported backup or bootstrap paths after installation. See [`docs/WORKFLOW-RECOVERY-IMAGE.md`](docs/WORKFLOW-RECOVERY-IMAGE.md) and [`docs/BACKUP-AND-RESTORE.md`](docs/BACKUP-AND-RESTORE.md).

## Safety and verification limits

The project remains **NO-GO** for formatting, repartitioning, USB writing, or migrating a physical disk. The current blockers include independent recovery, full-restore proof, an expanded VM matrix, live-media hardware qualification, recovery/dual-boot rehearsal, and a separate exact-device approval.

The strongest current evidence is scoped as follows:

- the hardware-target ISO candidate passed structural checks;
- a corrected, separate VM-only ISO installed and first-booted under a recorded BIOS/QEMU method;
- selected installed files and enablement links in that VM matched the declared source/policy;
- a separate live Nobara host run recovered one observed `rtw89` firmware fault without a module unload or observed kernel oops.

It does **not** prove UEFI-installed-system behavior, physical-media validity, complete workstation restoration, general Wi-Fi reliability, byte-identical rebuilds, hardware-installation readiness, or release certification. The full gate ledger is [`docs/PREFORMAT-GO-NO-GO.md`](docs/PREFORMAT-GO-NO-GO.md).

## Repository map

- `kickstart/` — interactive hardware-target source and isolated VM-only fixture.
- `scripts/` — build, payload assembly, validation, backup, and fail-closed support tooling.
- `overlays/` — files installed by the candidate payload.
- `manifests/` — package and source-to-installed-component declarations.
- `tests/` — static and behavioral boundary checks.
- `docs/` — design, recovery, installation, and decision records.
- `receipts/public/` — sanitized, non-secret local evidence.

## Contributing and use

This is currently a source/prototype repository, not a general-purpose operating-system distribution. Treat every change that affects storage, boot, firmware, credentials, network policy, or installer behavior as safety-sensitive. Start with [`AGENTS.md`](AGENTS.md), then run the Quick Start validation before proposing a change.

No license file has been selected or published in this snapshot; do not assume permission to redistribute or reuse the source or release asset beyond the repository's visible terms until a maintainer adds one.

## Further reading

- [Workflow Recovery Installer](docs/WORKFLOW-RECOVERY-IMAGE.md)
- [Pre-format GO/NO-GO ledger](docs/PREFORMAT-GO-NO-GO.md)
- [Build and install notes](docs/BUILD-AND-INSTALL.md)
- [Backup and restore boundary](docs/BACKUP-AND-RESTORE.md)
- [Design](docs/DESIGN-v0.2.md)
