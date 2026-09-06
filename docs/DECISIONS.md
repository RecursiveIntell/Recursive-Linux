# Decision Register

| ID | Decision | State | Rationale / reopening trigger |
|---|---|---|---|
| D-001 | Latest stable Fedora conventional minimal host for v1; currently Fedora 44 | admitted | User reconfirmed on 2026-08-21. Fedora’s official releases feed and download page identify Fedora 44 (44-1.7, released 2026-04-28) as current stable. Recheck immediately before media/artifact freeze; upgrade the target only to a newer stable release after rerunning package, Kickstart, VM, and hardware gates. |
| D-002 | Practical-minimal KDE Plasma Wayland | admitted | Preserves recovery and familiar controls; XWayland retained for automation. |
| D-003 | External HDD before internal migration | superseded | Superseded by D-016. The WD/exFAT drive is backup-only and must not be repartitioned or receive an OS. |
| D-004 | 128 GB USB is rescue/installer or constrained proof only | admitted | Selected roots total ~129.6 GiB before filesystem overhead; flash endurance is weak for daily development. |
| D-005 | Nobara may be erased only after backup and external qualification | superseded | Superseded by D-017. “External qualification” is now clean VM certification plus non-destructive live-USB hardware qualification; formatting also requires full restore and a separate exact-device approval. |
| D-006 | Final internal target is Windows + Workbench | admitted | Required for software unavailable or inferior on Linux. Windows installs first. |
| D-007 | LUKS2 encryption required | admitted | User requirement. TPM/Secure Boot activation remains gated by recovery rehearsal. |
| D-008 | Personal and automation Chrome profiles are separate | admitted | Prevents agent automation from inheriting personal cookies/credentials. |
| D-009 | Tailscale is part of the connected baseline | admitted | Preferred remote transport and service exposure boundary. |
| D-010 | All named workflow profiles are available | admitted | Profiles are systemd/container policies, not separate full OS installs. |
| D-011 | Stock Fedora kernel always retained | admitted | Experimental kernel/runtime work must have a known-good rollback. |
| D-012 | Custom kernel features require measured ROI | admitted | Userspace/eBPF/systemd approaches win unless a reproduced defect requires a bounded upstream patch. |
| D-013 | Google Drive backup is selective under quota | admitted | Preserve anything not provably recoverable from GitHub; omit only strictly verified covered repos/rebuildable caches. |
| D-014 | Encrypted restic over rclone is preferred backup transport | proposed | Handles dedupe, resumability, filenames, metadata and integrity better than browser/raw Drive upload. Requires Drive OAuth and quota verification. |
| D-015 | One heavyweight semantic-memory owner | proposed | Current process sample indicates duplicate workers and avoidable memory pressure. Requires Hermes integration test. |
| D-016 | External WD HDD is backup-only; USB flash is installer/rescue/live qualification only | admitted | Explicit current user decision. No repartitioning or OS installation on the WD drive. Any USB write requires exact-device approval. |
| D-017 | Formatting is governed by `ULTIMATE-IMPLEMENTATION-PLAN-v1.0.md` Gate F | admitted | No destructive action until source preservation, full restore, off-device recovery, clean VM, stack E2E, hardware, recovery-media, hostile-audit, and exact-device gates pass. Formatting remains a separate approval. |
| D-018 | Hermes sessions and semantic memory have independent lifecycle owners | admitted | `~/.hermes/state.db` is session/FTS state. Semantic memory, context archives, governed procedures, and Workflow-memory must not share a generic pruning path. |
| D-019 | Agent Graph uses one keyed daemon and Unix-socket proxies | proposed | Multiple direct processes sharing one graph directory are not an admitted durable topology. Requires staged daemon build, disposable keyed-store tests, persistence/tamper tests, and rollback before cutover. |
| D-020 | v1 hardware facts are the 2026-07-26 live inventory | admitted | Ryzen 7 7730U, 14 GiB RAM, 476.9 GiB NVMe, AMDGPU, RTL8852BE-VT; stale conflicting values are non-authoritative. |
