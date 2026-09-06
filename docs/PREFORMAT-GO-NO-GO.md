# Pre-format GO/NO-GO verdict

**Evidence cutoff:** 2026-09-06
**Scope:** the interactive hardware-target installer candidate and any later Fedora Workbench migration
**Verdict:** **NO-GO — do not format, repartition, write installer media, or migrate a physical disk.**

## What the current evidence supports

- The current local source tree passed its project validator and 34 unit tests at the stated evidence cutoff.
- Both Kickstart source files passed Fedora 44 `ksvalidator` during the recorded validation work.
- A locally constructed installer candidate passed static checks: BIOS and UEFI El Torito entries were found, boot configuration referenced the embedded Kickstart, the embedded payload hash matched the locally assembled payload, and `checkisomd5` reported success.
- A separate destructive VM-only fixture completed installation and first boot under a recorded BIOS/QEMU validation method. That result does not prove the attached hardware-target ISO installs or first-boots on any physical machine or through UEFI.
- The hardware-target Kickstart does not preselect disk clearing, automatic partitioning, a target disk, credentials, or an encryption secret. If an operator proceeds through the interactive installer, storage, partitions, bootloader state, and firmware-visible boot configuration can still change.
- No physical device, partition table, bootloader, or firmware variable was written during this work.

## Blocking gates

1. **Independent recovery:** retain a tested off-device recovery path before any destructive operation.
2. **Full restore proof:** complete a restore into an isolated filesystem and verify content, metadata, databases, and selected application-level behavior.
3. **Source/artifact lineage:** bind a reviewed source commit or tag to the published asset and retain the clean-rebuild limitation.
4. **VM matrix:** run repeated disposable install, update/reboot, disk-variant, failure-injection, and rollback cases.
5. **Hardware qualification:** run non-destructive live-media checks for Wi-Fi, suspend/resume, graphics, audio, peripherals, thermals, and storage on the exact target hardware.
6. **Recovery and dual-boot rehearsal:** qualify recovery media, firmware boot behavior, partition planning, and rollback before migration.
7. **Architecture admission:** resolve optional runtime-owner choices through explicit source and validation evidence; do not let the installer choose implicitly.
8. **Exact-device authorization:** record a stable device identity, model, capacity, and current mounts; obtain separate approval before any physical-media write or installation.

## Allowed next work

- Commit and publish the reviewed source with an explicit artifact boundary.
- Run additional disposable VM trials and failure injection.
- Perform non-destructive live-media qualification.
- Improve the reproducibility chain with a clean rebuild directly from official Fedora input.
- Prepare a separate device-identity receipt for a future approved USB-media action.

## Forbidden until the gates pass

- `mkfs`, partition-table changes, block-device writes, bootloader installation, firmware-variable changes, Secure Boot enrollment, backup pruning, remote deletion, or internal-disk migration.

A future GO evidence record still does not authorize a physical write. That remains a separate, exact-device operator decision.
