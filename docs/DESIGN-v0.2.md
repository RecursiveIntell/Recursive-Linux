# Hermes Workbench OS Design v0.2

> **SUPERSEDED BASELINE — DO NOT IMPLEMENT DIRECTLY.** The canonical implementation and pre-format gates are now in `docs/ULTIMATE-IMPLEMENTATION-PLAN-v1.0.md`. This document remains historical design input; conflicting hardware facts, external-media roles, council claims, and readiness language are non-authoritative.

**State:** proposed; live-host preflight partly verified; no installer or disk mutation yet.

## 1. Product definition

Hermes Workbench OS is a reproducible Fedora-based personal workstation profile—not an unsupported distro fork. It optimizes one laptop for Hermes Desktop, Chrome, governed local memory/control services, remote compute, evidence-led development, and isolated experiments while preserving a stock Fedora recovery path.

### Primary outcomes

1. Hermes remains responsive under builds, indexing, and local model activity.
2. Canonical work survives OS loss and can be restored independently of GitHub.
3. Risky toolchains/apps run in explicit, disposable profiles.
4. Networking and remote authority are visible and mode-scoped.
5. Updates, kernel experiments, and installations have mechanical rollback.

### Known gaps requiring design attention

A parallel quality council identified these critical design gaps (see `receipts/quality-council-report.md`):

- **Security:** TPM PCR 7 binding, initramfs signing/UKI, Kernel Lockdown, LUKS recovery key escrow, IOMMU Wi-Fi isolation, systemd sandboxing for network daemons.
- **Runtime:** MemoryHigh (not MemoryMax) for cgroup reclaim, CPUWeight over CPUQuota, add IOWeight.
- **Build:** Dependency pinning by hash (SBOM), containerized build environment.
- **Install:** Idempotency for interrupted partitioning, block-level pre-install snapshot.

These are design-stage findings and do not block the initial external-media prototype, but they are admitted requirements for internal dual-boot readiness.

- Gaming parity with Nobara.
- A permanently divergent kernel without a measured defect and regression test.
- All developer SDKs installed into the host.
- A locked kiosk that removes recovery access.
- Silent cloud upload, secret inclusion, or unattended disk selection.

## 2. Verified constraints

- HP 15-fc0xxx, Ryzen 7 7730U, AMDGPU, Realtek RTL8852BE, TPM 2.0.
- 14 GiB usable RAM; Hermes-related processes sampled at roughly 4.94 GiB RSS.
- One 476.9 GiB internal NVMe is fully partitioned for Nobara; free capacity is inside Btrfs.
- Realtek `rtw89_8852bte` produced a firmware crash on the live host despite power workarounds.
- Selected personal/state/source roots total about 129.6 GiB before dedupe and selective exclusions.
- 89 Git repositories were discovered under `~/Coding`; 29 were dirty and at least 166 status entries were untracked.
- No external block device was attached during preflight.
- Google Drive network access exists, but no rclone configuration or gog authentication exists.

## 3. Layer architecture

### Immutable-by-policy host layer

- Fedora 44 conventional RPM host for v1.
- Stock signed Fedora kernel always installed and bootable.
- LUKS2, Btrfs, SELinux enforcing, firewalld.
- Minimal KDE Plasma Wayland, SDDM, XWayland compatibility.
- NetworkManager, PipeWire/WirePlumber, BlueZ when profile-enabled.
- Podman/Toolbox boundary for toolchains.

### Hermes host-integration layer

- Hermes Desktop.
- One heavyweight semantic-memory owner with thin MCP clients.
- `cua-driver` and separate Chrome Automation profile.
- Hermes gateway, mnemes route, Agent Graph MCP and Tailscale.
- Systemd user slices/targets with explicit memory/CPU/IO budgets.

### Workload layer

Named containers and targets:

- `core`: Hermes UI, memory owner, CUA.
- `connected`: gateway, mnemes and Tailscale connectivity.
- `experimental`: disposable high-risk application/test environment.
- `esp32`: ESP-IDF, PlatformIO, serial/USB rules.
- `android`: Android SDK/NDK and device bridge.
- `godot`: Godot and project-specific tooling.
- `ml-research`: Python/UV, benchmark dependencies, optional local inference.
- `media`: codecs and creation tools omitted from baseline.
- `travel`: conservative power/network/background policy.
- `privacy`: remote gateways and optional egress disabled.
- `recovery`: no Hermes autostart; terminal, files, networking and restore tools only.

Profiles are service/toolchain policies, not separate user identities. Containerized profiles may use dedicated home directories where isolation pays for itself.

## 4. Kernel and runtime strategy

### Baseline

Use stock Fedora kernel plus current firmware first. Capture boot, Wi-Fi, suspend, latency, power, PSI and memory receipts. A custom kernel candidate cannot become default until it beats this baseline and survives rollback tests.

### High-ROI candidates

1. **Hermes pressure governor:** consumes PSI and systemd cgroup state; pauses/stops optional targets before interactive memory pressure becomes swap thrash.
2. **`sched_ext` workload policy:** prioritize Hermes UI, audio and automation; constrain background builds/model workers. Keep stock scheduler selectable at boot and runtime.
3. **Wi-Fi crash witness:** persist firmware-reset telemetry and attempt bounded NetworkManager/module recovery. Backport an upstream `rtw89` fix only after reproducing on current Fedora kernel+firmware.
4. **Measured boot:** signed UKI, TPM-bound LUKS unlock plus offline recovery key, and update/boot receipts after external-media qualification.
5. **Cgroup-scoped network policy:** Privacy and Travel modes restrict agent-service egress/inbound exposure without disabling the entire desktop.
6. **Power policy:** one controller coordinates AMD P-state EPP, platform profile, display timeout, boost and workload targets. Do not stack TLP, tuned-ppd and desktop power policy blindly.

### Rejected until measured

- PREEMPT_RT desktop kernel.
- non-upstream CPU scheduler patches;
- custom filesystem or block scheduler;
- blanket hugepages/KSM;
- custom AMDGPU patches;
- removing kernel security mitigations.

## 5. Browser/session design

- Plasma remains Wayland-native.
- `Chrome Personal` uses the normal profile and no automation debugging interface.
- `Chrome Automation` uses an independent profile, no personal cookies, bounded permissions and XWayland until native-Wayland CUA click/type/readback is proven.
- Hermes starts prominently but terminal, files, settings and recovery remain accessible.

## 6. Storage and boot sequence

### Phase A — external HDD

Use the external HDD as a fully independent encrypted install with its own EFI System Partition. Select it through the HP firmware boot menu. Do not alter internal partitions or reuse the internal EFI partition.

The 128 GB USB 3.0 flash drive is installer/rescue media or a constrained proof image only. It is smaller than the current selected working set and has inferior random-write endurance.

### Phase B — internal Windows + Workbench

Only after backup/restore and external qualification:

1. obtain and verify Windows and Fedora recovery/installer media;
2. record firmware settings and recovery keys;
3. erase Nobara with explicit approval;
4. install Windows first;
5. shrink Windows from Windows tooling;
6. install Workbench into explicitly identified free space without clearing Windows partitions;
7. retain independent boot entries and recovery media;
8. enable BitLocker/Secure Boot/TPM features only in an admitted order with both recovery keys available.

Provisional internal sizing: Windows 180–220 GiB; Workbench 220–260 GiB. Final sizing depends on the selective backup report and whether large project/model data stays remote/external.

## 7. Backup contract

Use encrypted restic snapshots transported by rclone to Google Drive. Upload priority:

1. non-Git personal data;
2. SQLite-consistent Hermes/control-plane state;
3. dirty/untracked/local-only/unpushed repositories and unknown ignored artifacts;
4. selected app/key state under encrypted backup;
5. clean, fully GitHub-covered repositories only if quota permits.

Closure requires snapshot ID, repository check, remote size/inventory, deterministic sample restore, hash parity and documented possession of the recovery password outside the laptop.

## 8. Security model

- Secrets never enter Git, Kickstart, ISO, logs or receipts.
- OAuth and backup credentials live in the desktop keyring or mode-0600 client configuration.
- Root remains locked; the human user receives explicit admin authority.
- Remote services bind loopback or Tailscale unless an admitted LAN rule exists.
- Experimental services run in dedicated slices/containers with resource and egress limits.
- Secure Boot/TPM enrollment is deferred until external qualification and recovery rehearsal.

## 9. Gates

| Gate | Required evidence |
|---|---|
| G0 source protection | selective manifest, Drive quota, encrypted repo initialized, restore password held separately |
| G1 backup | restic snapshot/check, remote reconciliation, sampled restore/hash parity |
| G2 image | Kickstart validation, package resolution, VM install/boot/update/rollback |
| G3 external media | exact device receipt, SMART/throughput, encrypted install, stock-kernel boot |
| G4 hardware | Wi-Fi soak, suspend loops, audio/video, touch, Chrome CUA, battery/thermal baseline |
| G5 custom runtime | pressure/scheduler/Wi-Fi candidates beat baseline and rollback cleanly |
| G6 internal migration | Windows media/recovery ready, explicit erase approval, dual-boot acceptance |

No later gate can retroactively satisfy an earlier one.
