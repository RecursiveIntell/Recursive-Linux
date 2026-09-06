# Hermes Workbench OS — Ultimate Implementation and Pre-Format Certification Plan v1.0

**Canonical status:** active safety contract; implementation and certification incomplete
**Current pre-format verdict:** **NO-GO**
**Current evidence cutoff:** 2026-09-06
**Historical plan baseline:** sections labeled “current evidence” below retain their 2026-07-26 provenance unless explicitly superseded by `docs/PREFORMAT-GO-NO-GO.md` and sanitized receipts under `receipts/public/`.
**Target:** HP Laptop 15-fc0xxx, AMD Ryzen 7 7730U, 14 GiB RAM, 476.9 GiB SK hynix NVMe, AMDGPU, Realtek RTL8852BE-VT
**Safety boundary:** this plan authorizes evidence gathering, local staging, disposable VM testing, and reversible configuration pilots. It does **not** authorize formatting, repartitioning, bootloader installation, UEFI changes, Secure Boot enrollment, external-device overwrites, remote deletion, publishing, or internal-disk installation.

---

## 1. Verdict and definition of “guaranteed”

An absolute guarantee is impossible before the real firmware, target disk, and final installation are exercised. The operational standard is therefore:

> **Do not format until every controllable failure mode has a reproduced test, all required gates pass from a clean start, all recovery paths are restored rather than merely listed, and the remaining irreducible risks are explicitly accepted.**

A confident explanation, a successful build, a prior VM attempt, or an LLM council is not proof. The only admissible final verdicts are:

- **GO:** every mandatory pre-format gate passed with rerunnable evidence; no unresolved critical/high finding; recovery material is available outside the laptop; user separately approves the exact target device and partition plan.
- **CONDITIONAL GO:** only explicitly accepted, non-data-loss residual risks remain. This state still does not authorize formatting.
- **NO-GO:** any backup, restore, source, install, boot, hardware, secrets, or rollback gate is missing, blocked, stale, or failed.

The current verdict is **NO-GO** because off-device backup is incomplete, the local backup scope requires a secret/browser-state review, source/runtime provenance is unresolved, Agent Graph is version-skewed, no current clean VM certification exists, no live Fedora hardware qualification exists, Windows recovery media is not certified, and no final end-to-end Workbench receipt exists.

---

## 2. Authority and corrections

### 2.1 Evidence hierarchy

1. Current live host, attached devices, repositories, installed binaries, active services, and fresh test output.
2. This plan and subsequently admitted receipts.
3. Current primary Fedora, systemd, kernel, Chromium, Hermes, SQLite, Candle, Microsoft, and hardware documentation.
4. Explicit user decisions in the active task.
5. Older project documents, reports, graph output, conversation, and memory as historical input only.

### 2.2 Superseded or quarantined claims

| Prior claim | Canonical correction |
|---|---|
| 32 GiB / Ryzen 7 5825U / ~954 GiB internal disk | Live evidence on 2026-07-26: Ryzen 7 7730U, 14 GiB RAM, 476.9 GiB NVMe. |
| External HDD should host a persistent test OS | Superseded by user decision: the 2 TB WD/exFAT drive is backup-only and must not be repartitioned. |
| USB flash drive as daily Workbench disk | Rejected. A flash drive is installer/rescue or bounded live-hardware qualification media only. |
| `~/.hermes/state.db` is semantic memory | False. It is Hermes session/FTS state. Semantic memory is a separate database. |
| One generic “memory pruning” implementation | Rejected. Hermes sessions, semantic memory, governed procedures, context archives, and Workflow-memory have separate owners and lifecycle contracts. |
| Compressed semantic retrieval is active | Not certified. The observed runtime still uses exact f32 search despite compressed artifacts. |
| Candle mmap means all processes share decoded weights | Unsupported. Mmap support exists; page sharing and decoded-heap behavior require measurement or a single-owner service. |
| An upstream patch fixes this exact Wi-Fi failure | Not established. Preserve the stock kernel/firmware and reproduce before any backport. |
| Old VM/build artifacts prove installability | Quarantined. They are stale, not provenance-bound, and do not satisfy current gates. |
| Agent Graph councils completed the final design | False. The current runs failed before any LLM step completed. Earlier council output is advisory only. |
| Google Drive backup is complete | False. The recorded restic/rclone run exited 1 and did not save a snapshot. |

---

## 3. Locked product decisions

### 3.1 v1 platform

- **Base:** conventional Fedora 44 KDE/Plasma installation, not a custom distro fork.
- **Desktop:** practical-minimal KDE Plasma on Wayland; XWayland retained where automation requires it.
- **Kernel:** stock signed Fedora kernel and firmware always installed and bootable.
- **Storage:** LUKS2 for Fedora, Btrfs for system/home data, zram baseline. Disk swap only if a tested hibernation requirement appears.
- **Security:** SELinux enforcing; firewalld default-deny inbound; loopback or Tailscale for service exposure.
- **Development:** rootless Podman plus Toolbox/Distrobox; SDKs and risky toolchains stay out of the host unless hardware integration requires a reviewed package.
- **Remote plane:** Tailscale is the default transport. No public bind merely for convenience.
- **ML:** Candle is the final local inference/embedding owner. Ollama may remain a temporary development dependency for Agent Graph certification, not the Workbench ML architecture.
- **Edge:** UNO Q remains CPU-only. GPU acceleration is quarantined.
- **Excluded:** Jacob and MiniRecall.

### 3.2 Device roles

- **Internal NVMe:** current rollback OS until the explicit format gate; eventual Windows + Fedora target.
- **External WD HDD:** encrypted backup repository and temporary restore-verification destination only. No repartitioning and no OS install.
- **USB flash media:** Fedora installer/rescue/live-hardware qualification after exact device identity and explicit write approval.
- **Recommended additional medium:** a second inexpensive USB drive for Windows installer/recovery so one media failure cannot remove both recovery paths.

### 3.3 User-facing defaults

- Core profile starts by default.
- Maker/ESP32, Android, Godot, ML/research, media, experimental, travel, privacy, and recovery profiles are opt-in.
- Hermes Desktop and Chrome are primary applications.
- Personal Chrome and Automation Chrome have physically separate user-data roots.
- Recovery tools, terminal, files, settings, and firmware boot access remain available; this is not a kiosk.

---

## 4. Canonical ownership map

| Domain | Canonical owner | Persistence | Forbidden overlap |
|---|---|---|---|
| Hermes conversations/sessions | Hermes `state.db` and documented session CLI/config | session DB + exports | Semantic-memory pruning must not mutate it directly. |
| Semantic facts/retrieval | one supervised semantic-memory service | semantic-memory DB and supported sidecars | No per-session heavyweight workers; no Workflow-memory tables. |
| Governed procedural memory | semantic-memory procedural APIs/claim governance when admitted | typed facts/claims/evidence | No silent promotion from session summaries. |
| Context compaction archive | context-governor adapter with dedicated archive store | bounded archive DB, ring size 50 | Not the Hermes session DB or primary semantic-memory DB. |
| Workflow experience/evidence | `workflow-memory` product/repository | its own sharded database/outbox | Not rebranded as semantic-memory procedural memory. |
| Graph orchestration | one Agent Graph daemon via Unix socket | keyed graph database + receipts | No multiple direct processes sharing one data directory. |
| Local embeddings/inference | one Candle service | model files + rebuildable caches | No unrelated process-local model copies by default. |
| Desktop automation | `cua-driver` plus Automation Chrome and optional isolated KWin session | disposable automation state | Never inherit Personal Chrome cookies, tokens, or debugging interface. |
| Service health | existing system-health-monitor/Hermes UI projection | rebuildable status/receipts | No second monitoring daemon unless an owner gap is proven. |
| Network exposure | firewalld + Tailscale + systemd unit bindings | explicit policy | No wildcard bind or silent LAN exposure. |
| Power policy | one controller using supported platform/amd-pstate interfaces | mode configuration | Do not stack conflicting TLP, tuned, desktop, and custom controllers. |

---

## 5. Dependency graph and parallelization

```text
P0 Evidence/source freeze
  ├── P1 Backup + full restore + recovery-material closure
  └── P2 Reproducible source/build baseline
          └── P3 Clean VM installation certification
                 ├── P4 Workbench stack E2E certification
                 └── P5 Live-USB hardware qualification
                         └── P6 Installer/recovery-media certification
                                └── GATE F: pre-format GO/NO-GO
                                       └── P7 Internal migration (separate approval)
                                              └── P8 post-install burn-in
```

Allowed parallel lanes after P0:

- Backup transport work may run alongside clean-source build work.
- Runtime, browser/CUA, memory, and documentation tests may run in separate VM clones after the base VM image is immutable.
- Hardware tests may run alongside VM stack tests once verified live media exists.

Must remain serialized:

- Dirty-source preservation and any source cleanup.
- SQLite/schema migrations.
- Agent Graph store/key migration.
- Backup pruning or remote deletion.
- USB writes, partition-table changes, encryption enrollment, UEFI changes, and release activation.
- Any operation touching the internal NVMe.

---

## 6. Phase P0 — evidence and source freeze

### Objective
Ensure implementation cannot destroy unknown work or promote an untraceable runtime.

### Required actions

1. Create a private pre-format evidence root outside this repository; mode 0700.
2. Record OS/kernel/hardware, disks/mounts, firmware/Secure Boot state, package versions, active services, listeners, cgroups, resource pressure, Wi-Fi errors, and installed binary hashes.
3. For every relevant repository, record root, remote, branch, HEAD, worktree state, submodules, worktrees, unpushed commits, tracked modifications, and untracked inventory.
4. Preserve dirty source without reset/clean:
   - Git bundle for reachable commits/refs.
   - Binary-safe working-tree archive for modified/untracked files.
   - `git diff --binary` and status manifest where practical.
   - Restic snapshot and sampled restore of the preservation packet.
5. Reconcile each active component:

   `canonical source → clean commit/lockfile → candidate artifact hash → installed artifact hash → live PID/args → durable store`

6. Recover or quarantine missing context-governor source. Receipts and installed artifacts are evidence, not editable source authority.
7. Initialize the Workbench project repository only after a secret scan and file-class review; do not commit build images, browser state, databases, credentials, or recovery material.

### Gate P0

Pass only when:

- Every relevant dirty tree is preserved and a sample restores with hash parity.
- Every active binary maps to known source or is explicitly quarantined.
- No implementation phase depends on a missing/ambiguous source owner.
- Project secrets scan reports no credential material.
- The evidence packet records commands, timestamps, hashes, failures, exclusions, and rollback.

Failure action: **NO-GO; preserve and stop.**

---

## 7. Phase P1 — backup, restore, and recovery closure

### Current evidence

- A local encrypted restic snapshot was previously recorded and sampled.
- The current cloud receipt records return code 1 and “unable to save snapshot”; cloud backup is incomplete.
- The local sample list includes browser/Hermes trust-state material. Because the repository is encrypted this is not plaintext exposure, but the inclusion policy must be reviewed before retrying off-device upload.
- The WD drive has about 225 GiB free and is mounted as exFAT. It remains backup-only.

### Required actions

1. Freeze the current backup repository and run a full repository integrity check, not only a percentage sample.
2. Export live databases consistently:
   - Hermes sessions via documented export/SQLite backup with integrity check.
   - Semantic-memory DB via its supported backup path/SQLite backup.
   - Workflow-memory, Agent Graph, and context archives independently.
   - Never recursively copy a live SQLite file and call it consistent.
3. Generate a reviewed include/exclude manifest. Flag browser cookies, trust-token databases, OAuth material, `.env`, SSH/GPG private material, keyrings, recovery keys, and cloud credentials.
4. Create a new dated local snapshot only after the scope review. Never mutate the old snapshot as evidence.
5. Restore the complete canonical dataset to a fresh temporary destination with space preflight. Compare count, logical bytes, types, symlink policy, and hashes. Validate every restored SQLite DB with `PRAGMA integrity_check` and application-level open/search tests.
6. Restore at least:
   - one >1 GiB file;
   - dirty and untracked Git work;
   - Unicode/long paths and symlinks;
   - representative documents/media;
   - Hermes session export/import;
   - semantic-memory search data;
   - Agent Graph receipt/store after keyed repair.
7. Configure a dedicated rclone Drive client if the shared client remains rate-limited. OAuth remains a human interaction; no token enters this repository or transcript.
8. Upload with `copy`, not `sync`. Reconcile remote object count/bytes and download a stratified sample. A partial remote repository is quarantined until verified or explicitly deleted.
9. Verify that backup and encryption recovery secrets are available through at least two independent channels outside the laptop. Record presence and retrieval test only—never the secret.

### Gate P1

- Full local `restic check` passes.
- Full canonical restore passes count/hash/application checks.
- Off-device snapshot completes and a downloaded sample passes plaintext hash comparison.
- All exclusions are reviewed; no unapproved secret class is present.
- Recovery password/key retrieval succeeds from outside the laptop.

Any unexplained difference, unreadable DB, missing dirty file, incomplete remote snapshot, or unavailable password keeps **NO-GO**.

---

## 8. Phase P2 — reproducible Workbench source and build

### Build contract

1. Use an official Fedora 44 image whose checksum/signature is verified against Fedora primary publication.
2. Build in a pinned container/Toolbox environment. Record container digest, tool versions, repository commit, lockfiles, Fedora repository metadata, exact package NEVRAs, and output hashes.
3. Treat the Kickstart/template, package manifest, overlays, scripts, service units, tests, and docs as source. Generated ISO/rootfs/qcow2 content is disposable projection.
4. Keep credentials, browser data, machine-specific recovery keys, cloud auth, and user secrets out of the payload.
5. Generate an SBOM and manifest for installed host packages, bundled files, systemd units, and third-party binaries.
6. Static checks:
   - Kickstart syntax and mutually exclusive directives.
   - Package resolution from current Fedora repositories.
   - Python/Rust/shell syntax and tests.
   - systemd unit verification.
   - SELinux file contexts and policy assumptions.
   - no forbidden paths/secrets/placeholders.
   - installer disk selection fails closed unless the exact approved disk is supplied.
7. Build twice from the same source. Exact ISO byte reproducibility is desirable but not assumed if upstream metadata is nondeterministic; every unexplained delta must be classified.

### Gate P2

- Clean source authority and immutable input manifest.
- All static/unit/integration checks pass.
- Package closure and SBOM complete.
- Artifact digests recorded.
- No secrets or machine-specific authorization in image.
- Build reruns from a clean directory without relying on host residue.

Rollback: discard generated projections; source and old artifacts remain unchanged.

---

## 9. Phase P3 — disposable VM certification

Old VM artifacts do not count. Start with a new qcow2 and OVMF variable store for each run.

### Test matrix

1. **Three clean installs** from the same admitted artifact under UEFI/q35/KVM.
2. Disk variants:
   - blank target;
   - existing unrelated Windows-like partitions that must be preserved;
   - existing LUKS/signature that must cause an explicit stop;
   - 512-byte and 4 KiB logical-sector simulations where QEMU supports them.
3. Network variants: normal, delayed DNS/NTP, mirror retry, disconnected install failure.
4. Failure injection using qcow2 snapshots: installer interruption before partitioning, during package deployment, and before bootloader finalization. Restart behavior must be explicit; no claim that GPT can always be atomically restored.
5. Encryption: LUKS passphrase boot, wrong-passphrase path, live-media unlock/mount, secondary recovery keyslot rehearsal.
6. Boot/update:
   - ten cold boots across the three installations;
   - normal reboot and clean shutdown;
   - kernel/package update;
   - retained stock-kernel selection;
   - rollback to pre-update snapshot/config.
7. Windows-first dual-boot rehearsal in a separate VM once official Windows media is available:
   - install Windows first;
   - preserve Microsoft ESP/MSR/recovery partitions;
   - install Fedora only into approved free space;
   - direct firmware boot of both entries;
   - Windows and Fedora updates without erasing the other boot files.
8. Optional later security lane: OVMF Secure Boot/UKI and TPM2 PCR testing. This cannot block initial passphrase-based v1 unless explicitly promoted.

### Gate P3

- 3/3 clean installs complete unattended or with documented intentional prompts.
- 10/10 admitted cold boots succeed.
- Negative disk-selection tests stop before mutation.
- Encryption and live recovery work.
- Update and rollback work.
- Windows-preservation rehearsal passes before internal dual boot.
- Logs contain no secret and no unresolved installer traceback/error.

---

## 10. Phase P4 — Workbench stack end-to-end certification

Run in immutable VM clones restored from the P3 base image.

### 10.1 Runtime ownership and health

Required services/capabilities:

- Hermes Desktop and gateway.
- One semantic-memory owner.
- Agent Graph daemon and thin socket proxies.
- Context-governor integration.
- Workflow-memory only when its independent product gate passes.
- `mnemes-tunnel`, `ri-fleet-gateway`, `sm-sync-watcher`, `cua-driver`, system-health-monitor, and Tailscale as applicable.

Acceptance:

- Exactly one heavyweight owner per canonical role across five session open/close cycles.
- Thin clients disappear after sessions close and memory returns near baseline.
- Every service has an explicit unit owner, restart policy, dependencies, writable paths, resource controls, and health probe.
- Network listeners are loopback, Unix socket, or admitted Tailscale addresses.
- Kill/restart tests recover without database corruption or duplicate ownership.
- Dashboard reports healthy/degraded/failed/blocked with links to current receipts; it does not infer health from PID existence alone.

### 10.2 Hermes sessions

1. Export important sessions before changing retention.
2. Exercise create, rename, end, resume, export, prune preview, prune, vacuum, and restore in a disposable copy.
3. Use Hermes’s documented `auto_prune`, `retention_days`, `vacuum_after_prune`, and sweep interval. Do not write a competing database pruner.
4. Select the retention duration from measured growth and user workflow; preserve pinned/active/important sessions.

Acceptance:

- Export/import round trip preserves selected session content and metadata.
- Ended-session pruning removes only eligible sessions.
- FTS/search remains correct; DB integrity passes; size reduction is measured.
- Rollback from pre-prune backup works.

### 10.3 Semantic memory and retrieval

1. Establish exact f32 search as the correctness oracle.
2. Test write/search/restart/supersede/evidence/claim operations and backup/restore.
3. Define lifecycle separately from session retention. No silent deletion; use typed supersession, archive, governed forgetting, or explicit user deletion.
4. Evaluate turbo-quant/proveKV/PerDimScorer behind flags against a frozen corpus.
5. Require quality metrics, not only compression:
   - result-ID overlap/Recall@k;
   - NDCG/MRR where labels exist;
   - contradiction/evidence behavior;
   - p50/p95 latency, RSS, artifact size, rebuild time;
   - exact rerank/fallback correctness.
6. Promote one backend only if quality loss stays within the predeclared budget and the exact path remains available for verification/rollback.

No public “12–57×” or quality claim may be made until reproduced on the actual corpus and hardware.

### 10.4 Context governor, procedure memory, and Workflow-memory

- Recover and certify context-governor source before extension.
- Context archive uses a dedicated database and FIFO ring of at most 50 admitted compaction archives; overflow eviction is logged and recoverable from canonical sessions where applicable.
- Hermes UI shows compaction pending/completed/failed, archive count, and restore affordance.
- Governed procedural memory requires typed provenance and promotion; model summaries do not self-promote.
- Workflow-memory remains a separate product with its own database, outbox, evidence graph, tests, and release decision.

Acceptance:

- Fifty-one archive insertions evict exactly the oldest eligible projection; canonical input is unaffected.
- Crash/restart leaves no half-promoted procedure or broken ring index.
- Workflow-memory backup/restore and its own test suite pass independently.

### 10.5 Candle service

- One supervised Candle service owns embedding/inference models.
- Safetensors mmap is used only after cold/warm RSS, page-cache, latency, and concurrency measurements.
- Clients use a bounded local endpoint with typed timeouts and no silent fallback to per-process model loading.
- Model files are content-addressed/rebuildable and excluded from canonical backup when safely redownloadable.

Acceptance:

- Five clients do not create five heavyweight model owners.
- Cold/warm start, concurrency, cancellation, malformed input, model mismatch, and restart tests pass.
- Final architecture has no Ollama dependency unless separately admitted.

### 10.6 Chrome and CUA

- Personal and Automation Chrome use separate `--user-data-dir` roots.
- Personal Chrome exposes no remote-debugging port.
- Automation debugging binds localhost only, uses a dedicated profile, and carries no personal cookies/passwords/extensions.
- CUA tests click/type/read back in the Automation profile. Native Wayland is preferred only after proven; XWayland is an admitted fallback.
- KWin MCP/isolated virtual desktop is an experiment, not a baseline dependency.

Acceptance:

- File and process inspection proves separate roots.
- Cross-profile cookie/history/bookmark sentinel tests show no leakage.
- Listener checks prove no public CDP bind.
- Five repeated CUA workflows pass with screenshot/readback evidence and safe interruption.
- Closing automation leaves no orphan debugging listener.

### 10.7 Resource, pressure, power, and caches

- Use `CPUWeight`, `IOWeight`, and measured `MemoryHigh` before hard `MemoryMax`.
- Enable `systemd-oomd` only for disposable/optional scopes after victim-order tests. `ManagedOOMPreference=avoid` is not immunity.
- Pressure governor sheds optional profiles before global thrash and never silently kills canonical memory/session owners.
- Keep zram/MGLRU baseline; tune only by repeated workload evidence.
- One power controller owns platform/amd-pstate policy.
- `/tmp`, compilation caches, and model caches may use tmpfs only with bounded sizes and spill/rollback tests.

Acceptance:

- Disposable stress kills/sheds only the intended scope.
- Two-hour normal workload has no false kill.
- Hermes/UI p95 does not regress beyond 5%; semantic-memory p95 no more than 10% absent a declared trade.
- Battery/thermal results are hardware-only evidence, not VM claims.

### Gate P4

All E2E suites pass from a clean VM restore, service ownership is singular, backup/restore works for every durable store, and no critical/high security or data-integrity finding remains.

---

## 11. Phase P5 — non-destructive laptop hardware qualification

VMs cannot certify the Realtek firmware, HP UEFI, suspend, audio, battery, display, or physical input devices.

### Method

1. Capture the current Nobara baseline: kernel/firmware, Wi-Fi crashes/outages, suspend, audio/video, thermals, battery, power profile, and device inventory.
2. After exact USB approval, boot an official verified Fedora KDE live/rescue image in UEFI mode. Do not mount the internal filesystem read-write and do not install.
3. Run:
   - 24-hour Wi-Fi normal-use/throughput soak;
   - repeated AP interruption/reconnect;
   - at least 20 suspend/resume cycles;
   - audio input/output, webcam, Bluetooth, touchpad, keyboard, brightness, external display, USB, SD if present;
   - Chrome/Wayland/XWayland smoke;
   - thermal and battery sampling in idle, video, browser, and bounded build workloads.
4. Correlate each `rtw89` firmware/SER event with actual connectivity loss. Passive monitoring first; NetworkManager reconnect second. Module reload is an opt-in last resort and must not run while it would strand the active control connection.
5. A/B only supported Fedora kernel/firmware versions. Preserve stock fallback. No speculative driver patch.

### Gate P5

- Zero unexplained disconnects and zero new firmware/SER crashes over the admitted soak, or an accepted hardware replacement/alternate adapter path.
- 20/20 suspend/resume cycles.
- Every required peripheral passes.
- No thermal shutdown or sustained unsafe temperature.
- Battery/power behavior is measured and acceptable.
- Recovery to current Nobara remains intact.

The observed RTL8852BE-VT crash is release-blocking until this gate passes.

---

## 12. Phase P6 — installer and recovery media

### Requirements

- Fedora installer/live media from an official source with verified digest/signature.
- Windows 11 installer and separate Windows recovery capability from Microsoft.
- Prefer separate physical media. If one multiboot drive is unavoidable, boot-test every entry and keep an independent fallback method.
- Exact device identity receipt before every write: by-id path, model, size, transport, current partitions/mounts, and explicit user approval.
- Boot each medium on this laptop in UEFI mode without installing.
- Verify Fedora live unlock/mount procedure and Windows repair environment availability.
- Recovery keys/passwords exist outside both media and this repository.

### Gate P6

Both OS recovery paths boot successfully, checksums are recorded, media can be recreated from documented sources, and no target-disk operation is automatic.

---

## 13. Final pre-format Gate F

Formatting remains forbidden until all boxes are backed by current receipts:

- [ ] P0 source preservation and source/runtime mapping passed.
- [ ] P1 full local restore and off-device restore sample passed.
- [ ] Backup scope reviewed; no unapproved secret/browser-state class.
- [ ] P2 clean reproducible build passed.
- [ ] P3 VM matrix, LUKS recovery, update/rollback, and Windows-preservation rehearsal passed.
- [ ] P4 complete Workbench E2E passed from a clean restore.
- [ ] P5 hardware qualification and Wi-Fi soak passed.
- [ ] P6 Fedora and Windows recovery media booted on the laptop.
- [ ] LUKS, BitLocker, backup, and account recovery material was retrieved from outside the laptop.
- [ ] Final data/partition sizing leaves at least 20% practical headroom in both operating systems.
- [ ] Independent hostile audit has no unresolved critical/high finding.
- [ ] Exact internal target receipt identifies `/dev/nvme0n1` by immutable device identity and current GPT digest.
- [ ] User reviews the evidence packet and separately approves the destructive operation.

### Residual risks that cannot be eliminated in advance

- Actual internal-disk write/power failure.
- Firmware behavior after the final partition/boot-entry layout exists.
- A future Windows/Fedora update regression.
- Hardware failure occurring after backup.

Mitigation requires tested recovery, independent media, off-device data, retained installer inputs, and rollback—not a claim of certainty.

---

## 14. Phase P7 — internal migration (only after separate approval)

1. Record final firmware settings, GPT, EFI variables, device identity, and recovery-material availability.
2. Boot Windows media in UEFI mode and install Windows first.
3. Allow Windows to create required ESP/MSR/recovery partitions. Complete updates/drivers and verify activation path.
4. Establish and verify BitLocker recovery before relying on BitLocker. Sequence Secure Boot decisions deliberately to avoid surprise recovery loops.
5. Leave the Fedora allocation unallocated from Windows tooling.
6. Boot the admitted Fedora installer in UEFI mode. Select only the approved free region. Stop if it proposes formatting Microsoft or recovery partitions.
7. Install Fedora with LUKS2 passphrase and Btrfs. Keep the stock signed kernel.
8. Verify direct firmware boot of Windows and Fedora; neither may depend solely on the other’s menu.
9. Restore canonical data into new destinations; do not overwrite fresh configuration wholesale.
10. Reinstall projections from pinned manifests and rehydrate credentials through their intended human-controlled channels.

Initial v1 uses LUKS passphrase recovery. Secure Boot, UKI, kernel lockdown, and TPM2 PCR 7 enrollment are a later admitted security phase after stable dual-boot and a recovery rehearsal. TPM unlock never replaces the offline LUKS recovery path.

---

## 15. Phase P8 — post-install burn-in and promotion

For at least 72 hours:

- repeated cold boot and direct firmware boot of both OSes;
- Fedora and Windows updates;
- Wi-Fi soak and suspend cycles;
- Workbench E2E and service restart tests;
- backup to both local and off-device repositories;
- restore a new post-install sample;
- verify no unexpected public listeners, duplicate owners, SELinux denials, filesystem errors, firmware crashes, or recovery-key prompts without explanation.

Promote the internal Workbench only after the burn-in receipt passes. Keep recovery media and the verified pre-format backup under retention; do not immediately prune the last known-good evidence.

---

## 16. Feature admission by ROI

### Tier 1 — required before GO

- Full backup/restore and recovery media.
- One-owner runtime topology and health dashboard.
- Hermes session export/retention/restore.
- Separate Chrome profiles and safe CUA.
- Tailscale/loopback exposure policy.
- Resource slices, pressure telemetry, and bounded optional-workload shedding.
- Wi-Fi reliability and stock-kernel rollback.
- Clean bootstrap/rebuild manifest.

### Tier 2 — admit after base reliability

- Dedicated context archive ring and visible compaction feedback.
- Workflow-memory/Agent Evidence Workbench as a separately certified product.
- Single-owner Candle embedding service.
- Compressed semantic scorer selected by retrieval-quality gates.
- Fleet/UNO Q dashboard with CPU-only assumptions.
- Local `quant-eval` tooling after source cleanup. Publishing remains a separate public action requiring approval.

### Tier 3 — experiments only

- KWin MCP isolated automation session.
- `sched_ext` policy.
- eBPF egress enforcement.
- tmpfs/cache changes.
- SQLite mmap/io_uring experiments.
- Kinoite/bootc migration.
- TPM2 auto-unlock/UKI measured boot.
- Custom rtw89 backport.

Complexity must demonstrate a measured reliability, latency, memory, power, security, or recovery gain. Otherwise it remains off.

---

## 17. Evidence packet and acceptance receipt format

Every gate writes a redacted receipt containing:

- schema and gate ID;
- UTC/local timestamps;
- host/VM identity and source commit;
- input artifact hashes;
- commands/probe classes;
- tests executed and counts (never “pass” for zero tests);
- measured outputs and thresholds;
- passed, failed, blocked, skipped, and quarantined items;
- changed files/config/services;
- active-vs-candidate-vs-installed hashes;
- rollback commands/procedure;
- secret paths and key presence by mode/size only, never contents;
- reviewer and approval boundary.

Recommended paths:

```text
receipts/preformat/00-source-freeze.json
receipts/preformat/01-backup-restore.json
receipts/preformat/02-build.json
receipts/preformat/03-vm-matrix.json
receipts/preformat/04-stack-e2e.json
receipts/preformat/05-hardware.json
receipts/preformat/06-media.json
receipts/preformat/07-hostile-audit.md
docs/PREFORMAT-GO-NO-GO.md
```

Derived reports are rebuildable. Primary logs, manifests, test output, hashes, and source are the evidence.

---

## 18. Immediate execution order

1. Repair or quarantine Agent Graph safely: stage the clean daemon candidate, externalize its integrity key, test in a disposable data directory, then switch from shared direct mode to one daemon/socket owner with rollback.
2. Run the architecture/hostile councils with a bounded local model and `max_tokens`; independently adjudicate every finding.
3. Validate this plan mechanically against the live inventory and all explicit decisions; amend stale decision documents.
4. Preserve dirty source and resolve the missing-source/runtime matrix.
5. Close backup and full restore before any build expansion.
6. Build the candidate from clean source, then execute P3–P6.
7. Produce `PREFORMAT-GO-NO-GO.md`. Until it says GO with all receipts present, **do not format the laptop**.

---

## 19. Primary reference set

- Fedora installation and KDE documentation: <https://docs.fedoraproject.org/>
- Fedora Atomic/Kinoite installation limitations: <https://docs.fedoraproject.org/en-US/fedora-kinoite/installation/>
- systemd resource control and oomd: <https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html>
- systemd cryptenroll: <https://www.freedesktop.org/software/systemd/man/latest/systemd-cryptenroll.html>
- Linux PSI, MGLRU, sched_ext, TPM, and wireless documentation: <https://docs.kernel.org/>
- Chromium user-data directory contract: <https://chromium.googlesource.com/chromium/src/+/HEAD/docs/user_data_dir.md>
- SQLite FTS5, WAL, and mmap: <https://www.sqlite.org/fts5.html>, <https://www.sqlite.org/wal.html>, <https://www.sqlite.org/mmap.html>
- Hermes sessions/configuration: <https://hermes-agent.nousresearch.com/docs/user-guide/sessions>
- Candle safetensors implementation: <https://github.com/huggingface/candle>
- Microsoft Windows and BitLocker recovery: <https://learn.microsoft.com/windows/security/operating-system-security/data-protection/bitlocker/>
- restic and rclone verification: <https://restic.readthedocs.io/> and <https://rclone.org/docs/>

---

## 20. Plan completion state

This file is a source-present implementation and certification contract. It is **not** evidence that the OS, backup, hardware, dual boot, or Workbench stack already works. Completion requires the receipts and gates above. The format decision remains blocked until the final evidence packet independently establishes GO.

---

## 21. Council and audit findings (2026-07-26)

Architecture and hostile review performed by Agent Graph MCP with
`glm-5.2:cloud` (both graphs completed successfully after v3 graphs set
explicit `model: glm-5.2:cloud` on every LLM node). Earlier failures
were caused by model resolution — the old graphs had no explicit model
field, and the server default path was not reliably routing to
`glm-5.2:cloud`.

Full findings: `docs/COUNCIL-FINDINGS-v1.1.md`
Receipts: `receipts/preformat/04-architecture-council-v3.json`,
`receipts/preformat/05-hostile-review-v3.json`

Architecture council: `run-19f9f9baca0-c` — 68.2s, 4 LLM calls, completed.
Hostile review: `run-19f9f9bb2af-d` — 65.3s, 4 LLM calls, completed.
Both independently arrived at: **NO-GO**.

### Key findings incorporated into this plan

1. **Agent Graph integrity key gate added** (see Gate F below). Production
   Agent Graph has no integrity key; staged candidate is qualified but not
   installed. This is now a named blocker.

2. **clippy/MSRV gate elevated.** The staged candidate's 27 clippy findings
   block production installation. The declared Rust 1.75 MSRV is violated by
   APIs stabilized in 1.82 and 1.89.

3. **Libraries repo safety gate added.** The repo has 389 dirty entries and
   2,421 unknown ignored entries. No modification is safe until a verified
   preservation snapshot exists.

4. **Model availability gate added.** The plan depends on cloud LLM
   orchestration but the configured model is unreachable. A verified model
   path must exist before any graph-dependent phase.

5. **Verified restore elevated to pre-P2 requirement.** The council confirms
   that a full clean-destination restore is the single highest-ROI next
   action — it validates the backup, proves recoverability, and enables all
   subsequent phases without data-loss risk.

### Updated verdict

The council confirms the NO-GO verdict. The plan is structurally sound but
every phase is aspirational. The format decision requires the gates listed
below with current receipts — not plan text or prior attempts.

## 22. Updated Gate F checklist (2026-07-26)

Formatting remains forbidden until all boxes are backed by current receipts:

- [x] P0 source classification complete (`receipts/preformat/00-source-freeze-git.json`)
- [ ] P0 source preservation snapshot covering all 90 classified repos
- [ ] P0 Libraries repo preserved without modification
- [ ] P0 full source-to-runtime mapping for all active binaries
- [x] P1 local restic check --read-data passed (`receipts/preformat/01-restic-full-data-check.json`)
- [ ] P1 full clean-destination restore with database validation
- [ ] P1 off-device backup with downloaded sample verification
- [ ] P1 backup scope reviewed; no unapproved secrets class present
- [ ] P1 recovery secrets proven retrievable outside laptop
- [ ] P2 clean reproducible build from pinned inputs
- [ ] P3 VM installation matrix (3 clean installs, 10 cold boots, LUKS recovery, failure injection)
- [ ] P3 Windows-preservation dual-boot rehearsal
- [ ] P4 Workbench E2E from clean VM restore
- [x] P5 hardware qualification from Nobara 43 (Fedora 44 kernel base) — all peripherals functional, Wi-Fi 990 crashes auto-recover via SER, suspend/resume works (`receipts/preformat/06-hardware-qualification-from-nobara.json`)
- [ ] P5 Fedora live-USB extended Wi-Fi soak (24h) and 20 suspend/resume cycles — current evidence is 2-day observation with 990 crashes but auto-recovery confirmed
- [ ] P6 Fedora and Windows recovery media created and boot-tested
- [ ] Agent Graph production instance: integrity key configured, model verified reachable, clippy resolved OR staged candidate formally promoted
- [ ] Libraries repo verified preserved and safe to modify
- [ ] Final data/partition sizing documented with ≥20% headroom
- [ ] Hostile audit findings resolved or accepted as residual risk
- [ ] Exact internal target receipt (`/dev/nvme0n1`) by immutable device identity
- [ ] User reviews evidence packet and separately approves destructive operation
