# Windows + Hermes Workbench: External-Media Qualification and Internal Dual-Boot Design

> **PARTIALLY SUPERSEDED — DO NOT INSTALL TO THE EXTERNAL HDD.** The WD/exFAT drive is backup-only by current user decision. Use `docs/ULTIMATE-IMPLEMENTATION-PLAN-v1.0.md` as the canonical authority. The internal Windows-first dual-boot and recovery discussion below remains historical design input and must pass the newer gates before use.

**Status:** proposed / source-present
**Safety boundary:** design only. No disk, UEFI, package, mount, or service changes were performed.

## 1. Executive decision

1. **Qualify Fedora Workbench externally first.** Prefer the external HDD for a persistent encrypted Workbench installation if it is a conventional USB 3.x HDD in good health and can remain connected during use. Use the 128 GB USB 3.0 flash drive primarily as installer/rescue media, not as the first-choice daily OS disk.
2. **Do not erase Nobara yet.** The internal NVMe is the rollback environment until backup closure, sampled restore, external Workbench qualification, and Windows installer readiness all pass.
3. **For the eventual internal migration, install Windows first into a deliberately sized partition, then install Fedora Workbench into the remaining space.** This lets Windows create its own Microsoft boot files and recovery partitions before Fedora is installed.
4. **Use one firmware-visible UEFI system, but keep OS boot files logically independent.** The cleanest practical layout is one shared ESP with separate `EFI/Microsoft` and `EFI/fedora` directories, plus independent UEFI entries. Do not allow either installer to format the other OS's ESP. A separate ESP per OS is possible only if the firmware reliably supports selecting both; it is not automatically safer.
5. **Encrypt each OS with its native mechanism:** Fedora Workbench with LUKS2; Windows with BitLocker after Windows is stable and its recovery key is escrowed. Keep recovery material outside this repository and away from installer media.

## 2. Current host evidence (read-only observation)

Observed from the live host on 2026-07-24:

- Internal NVMe: `/dev/nvme0n1`, 476.9 GiB, SK hynix BC901.
- Existing layout: 600 MiB EFI (`/dev/nvme0n1p1`, mounted `/boot/efi`), 2 GiB `/boot`, 457.9 GiB Btrfs root/home, 16.5 GiB swap.
- Root Btrfs: 458 GiB total, 287 GiB used, 167 GiB available (64% shown by `df`).
- Firmware is UEFI. Current Fedora entry is active; Windows and Kali entries exist but point at different GPT partition GUIDs and should be treated as **stale/unverified**, not proof that those installations remain present.
- TPM2 device is visible. Secure Boot is reported by task context as disabled/setup mode; this must be rechecked in the firmware and installer before migration.

This evidence is not a permission to modify the disk.

## 3. External-media qualification

### 3.1 HDD versus 128 GB flash drive

| Medium | Recommended role | Strengths | Risks / limits |
|---|---|---|---|
| External USB HDD | Persistent Workbench qualification and rollback system | Usually better sustained writes and endurance than cheap flash; large capacity for OS, containers, models, logs, and snapshots; lower cost/GB | Mechanical shock, slower random I/O, USB bridge/cable/power failure, must remain attached; verify SMART health |
| 128 GB USB 3.0 flash | Fedora/Windows installer, rescue, diagnostics; disposable test only | Small, portable, convenient | Consumer flash has opaque controller/wear-leveling, poor sustained/random write behavior, thermal throttling, finite write endurance, and only about 119 GiB decimal usable before partitions; persistent Workbench leaves little headroom |

A USB 3.0 label describes the interface, not NAND quality or sustained throughput. Do not infer SSD-like endurance from the connector. For a persistent desktop with Btrfs metadata, updates, browser caches, containers, and agent artifacts, the HDD is the safer first qualification medium **if its health and SMART counters pass**. A USB SSD would be preferable to both, but is not assumed available.

### 3.2 Minimum sizing

- **Installer-only:** 16 GB is normally enough for a Fedora installer image; reserve the 128 GB stick for this, Windows installation media, and rescue tools, with separate verified images or a multi-boot tool only after testing.
- **Persistent Workbench minimum:** 128 GB is a floor, not a recommendation. Allocate at least 60–80 GiB to the OS and leave 25–40 GiB free for updates, Btrfs metadata, logs, and rollback. It is unsuitable for a substantial model/container/cache workload.
- **Practical external target:** 256 GB minimum; 512 GB+ preferred. For the available HDD, reserve enough free space for Workbench, a test data set, and a separate backup area only if the backup is not the sole copy.

### 3.3 Non-destructive qualification gates

**Gate M0 — device identity (must pass before any write):** record `/dev/disk/by-id`, model, serial, size, transport, partition table, and a photo/label. Unplug unrelated disks. Require explicit approval naming the exact target device before writing an image or partition table.

**Gate M1 — media health:**

- HDD: read-only SMART health and long/extended test; no uncorrectable sectors or pending sectors; inspect USB bridge stability.
- Flash: identify controller/vendor if possible; perform a non-destructive read test. Do not use a destructive full-disk write test unless separately approved.
- Any disconnect, I/O error, reset, or unexplained filesystem error = **blocked/quarantined**.

**Gate M2 — installer integrity:** download Fedora Workbench and Windows media only from official sources; verify checksums/signatures where published; record URL, version, timestamp, and digest in a local receipt. Never put credentials or recovery keys on the media.

**Gate M3 — external install and boot:** after approval, install Fedora with LUKS2 to the identified external target, boot it on this machine in UEFI mode, confirm the internal NVMe remains untouched, and capture `lsblk`, `findmnt`, `bootctl`/UEFI state, `cryptsetup status`, SELinux enforcing state, network, suspend/resume, and USB reconnect behavior.

**Gate M4 — workload qualification:** run the actual Hermes Desktop/Workbench workflows, Chrome separate-profile policy, semantic-memory thin-client policy, developer toolchains, container/cache placement, updates, reboot, and recovery from an intentionally recorded unlock/boot procedure. Label this **external-media-verified** only when all pass.

**Gate M5 — backup and rollback:** verify a sampled restore from the backup set and prove the internal Nobara boot path still works. Until then, Nobara remains rollback.

## 4. Backup and recovery closure before internal changes

Create a manifest of required data and explicitly exclude secrets from the repository and installer images. Back up source trees, documents, SSH public material and separately protected private keys, browser/profile data as intentionally selected, Hermes configuration/state, semantic-memory data, package/config inventories, and encryption/UEFI recovery information.

Google Drive upload alone is not closure. Require:

- local manifest with path, size, count, timestamp, and hashes where practical;
- remote inventory and size/count reconciliation;
- sampled restore to a clean destination;
- opening/verifying representative source, document, Hermes, and memory artifacts;
- a written record of omissions, especially credentials/cookies/`.env` files;
- two independent recovery paths for BitLocker and LUKS recovery information.

## 5. Eventual internal Windows-first layout

The current 476.9 GiB disk cannot safely be “made dual boot” by shrinking blindly: roughly 287 GiB is in use and Btrfs free-space reporting is not the same as safely contiguous shrinkable tail space. First obtain a verified backup, boot the Windows installer in UEFI mode, and use a planned layout only after a dry-run/storage review.

### Recommended capacity envelope

For this workload, target approximately:

- **Windows:** 140–180 GiB, including its EFI/MSR/recovery partitions and future update headroom. Microsoft lists 64 GB as a minimum, not a comfortable development/desktop allocation.
- **Fedora Workbench:** 280–320 GiB for encrypted Btrfs root/home, containers, toolchains, semantic-memory data, caches, and snapshots.
- **ESP:** 512 MiB–1 GiB, FAT32, shared but never reformatted by the second installer.
- **Windows recovery/MSR:** let Windows create its required small partitions; do not delete them as “waste.”
- **Swap:** use zram by default; retain a disk swap area only if hibernation is a deliberate, tested requirement. Linux hibernation and BitLocker are separate concerns and should not share assumptions.

This is a planning range, not an instruction to repartition. If Windows plus Workbench cannot each retain healthy free space after a real capacity audit, expand the internal drive or defer migration rather than force a cramped install.

### Sequence

1. Finish backup/restore and external qualification gates.
2. Produce device and current-partition receipts; confirm UEFI mode, TPM2, Secure Boot state, firmware settings, and Windows license/activation path.
3. Create and verify Windows installer/rescue media. Install Windows first into the approved internal allocation, allowing it to create its own ESP/MSR/recovery partitions. Complete updates and drivers.
4. Before enabling BitLocker, connect the machine to the intended Microsoft account or approved escrow path and export/verify the recovery key through a separate protected channel. Test that the key is retrievable. Then enable BitLocker and record the protector/recovery receipt without storing the secret here.
5. Boot Fedora Workbench installer in UEFI mode. Select only the unallocated Fedora region. Use LUKS2 plus Btrfs; preserve the Windows ESP and all Windows recovery partitions. If the installer proposes formatting the ESP or deleting Windows partitions, stop.
6. Keep separate boot files: Windows under `EFI/Microsoft`, Fedora under `EFI/fedora`, with distinct UEFI entries. Fedora's boot menu may chain-load Windows, but either OS must remain bootable directly from the firmware menu. Do not rely solely on a GRUB-generated autodetection entry.
7. Verify both direct firmware boots, cold boots, updates, suspend/resume, Fedora unlock, Windows BitLocker unlock/recovery behavior, and rollback to the stock Fedora kernel. Mark **dual-boot-verified** only after the evidence packet is complete.

## 6. Encryption and Secure Boot interactions

- **LUKS2:** protects Fedora at rest but does not authenticate the boot chain by itself. Keep the passphrase/recovery material offline and test recovery before trusting the install.
- **BitLocker:** protects the Windows volume and commonly uses TPM measurements. Firmware/boot-order changes, Secure Boot changes, bootloader changes, or firmware updates can trigger recovery; that is expected, not evidence of data loss. Recovery material must be available before any bootloader or firmware work.
- **Secure Boot:** enabling it later can change which Fedora shim/kernel/modules are accepted and can trigger BitLocker recovery because measured boot state changes. Prefer Fedora's signed boot path and stock kernel. Do not enroll custom keys during this migration. Decide the final Secure Boot state before enabling BitLocker, or be prepared to suspend BitLocker (using Microsoft's supported procedure) before planned boot-chain changes and resume it afterward.
- **TPM2 is not a backup:** it is a hardware protector/measurement aid. It does not replace BitLocker recovery keys, LUKS recovery keys, or an offline backup.

## 7. Rescue and bootloader independence

Maintain:

- verified Fedora installer/rescue media;
- verified Windows installer and Windows recovery media;
- a separate offline copy of BitLocker recovery information;
- Fedora LUKS recovery material and a tested live-unlock/mount procedure;
- current partition/UEFI receipts and backup manifest;
- a known-good fallback boot choice in firmware.

Bootloader independence means: firmware can launch `\EFI\Microsoft\Boot\bootmgfw.efi` directly and Fedora's signed Fedora entry directly; changing Fedora's menu must not make Windows unbootable, and Windows feature updates must not be treated as permission to erase Fedora. A shared ESP is acceptable only with this directory/entry separation and a tested rescue path. If firmware proves unreliable with shared entries, revisit a separate-ESP design before installation; do not improvise after data is on disk.

## 8. Acceptance checklist and stop conditions

### Must pass before destructive approval

- [ ] Backup manifest, remote reconciliation, sampled restore, and omissions reviewed.
- [ ] External HDD/flash identity and health receipt captured.
- [ ] Fedora installer checksum/signature verified.
- [ ] Windows media created and independently boot-tested.
- [ ] BitLocker recovery path understood and tested after Windows installation.
- [ ] Fedora external Workbench is **external-media-verified**.
- [ ] Current Nobara boot and rollback procedure tested.
- [ ] User explicitly approves the exact internal target and planned partition sizes.

### Stop immediately if

- device identity is ambiguous;
- any health or I/O test reports errors;
- the installer is booted in legacy/CSM mode;
- either installer wants to format/delete an unrelated ESP/recovery partition;
- backup restore sampling fails;
- BitLocker recovery key cannot be retrieved;
- Fedora external qualification fails a required workload;
- free space is insufficient for both operating systems with headroom.

## 9. Primary sources

- Microsoft, Windows 11 requirements: https://learn.microsoft.com/en-us/windows/whats-new/windows-11-requirements
- Microsoft, Windows 11 specifications: https://www.microsoft.com/en-us/windows/windows-11-specifications
- Microsoft Learn, BitLocker overview: https://learn.microsoft.com/en-us/windows/security/operating-system-security/data-protection/bitlocker/
- Microsoft Learn, BitLocker recovery overview: https://learn.microsoft.com/en-us/windows/security/operating-system-security/data-protection/bitlocker/recovery-overview
- Microsoft Learn, BitLocker recovery process: https://learn.microsoft.com/en-us/windows/security/operating-system-security/data-protection/bitlocker/recovery-process
- Fedora Docs, Anaconda installation/manual partitioning: https://docs.fedoraproject.org/en-US/fedora/f34/install-guide/install/Installing_Using_Anaconda/
- Fedora Docs, dual boot/manual partitioning hazards (Silverblue guidance, applicable caution): https://docs.fedoraproject.org/en-US/fedora-silverblue/installation/
- systemd-boot documentation: https://www.freedesktop.org/software/systemd/man/latest/systemd-boot.html
- systemd Boot Loader Specification overview: https://uapi-group.org/specifications/specs/boot_loader_specification/

## 10. Evidence state

- **source-present:** primary-source links and local host observations recorded above.
- **proposed:** external target choice, capacity ranges, ordering, encryption, and acceptance gates.
- **not yet external-media-verified:** no external device was written or booted by this task.
- **not yet dual-boot-verified:** no internal partitioning, Windows installation, Fedora installation, UEFI modification, or BitLocker/LUKS activation was performed.
