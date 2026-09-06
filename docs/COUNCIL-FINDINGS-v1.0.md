# Council Findings — Hermes Workbench OS Plan v1.0

**Produced by:** deepseek-v4-pro (orchestrator model)
**Date:** 2026-07-26
**Authority:** Direct analysis — Agent Graph LLM path quarantined (see AG-LLM-QUARANTINE.md)
**Evidence cutoff:** 2026-07-26, ~17:00 UTC

## 1. Architecture Review

### Top 5 architectural risks (priority order)

#### Risk 1: No verified recovery path exists

**Severity:** CRITICAL
**Evidence:**
- Single restic snapshot `8f8efe0e` from July 24 on WD HDD (exFAT, 90% full).
- `restic check --read-data` PASSED — but this proves repository integrity, NOT restore capability.
- No clean-destination restore has been performed.
- No off-device copy exists (Google Drive backup exited 1).
- Recovery secrets not proven retrievable outside the laptop.
- The plan's P1 section acknowledges these gaps but provides no path to close them before formatting.

**Consequence:** If the internal NVMe is formatted and any restoration fails, data is permanently lost. The "guarantee" the user demands cannot exist without a verified restore.

**Fix:** Perform a full clean-destination restore to a temporary location, validate every SQLite database, compare file counts and hashes, THEN proceed. This is not deferrable.

#### Risk 2: The plan has no validated build artifact

**Severity:** HIGH
**Evidence:**
- No Kickstart has been built, tested, or installed in any VM.
- Zero current VM installations exist (old artifacts quarantined).
- The plan's P2 (build) and P3 (VM matrix) are entirely aspirational.
- The Wi-Fi firmware crash (rtw89_8852bte, 15 observed) means even a perfect build may be unusable on this hardware.

**Consequence:** The entire "Workbench OS" exists only as a document. Building it from the plan is an implementation project, not a verification step. The user has no evidence the plan can produce a working system.

**Fix:** Admit that the plan is a design contract, not a build artifact. The gap between "plan written" and "system built" is weeks of work, not a checkbox.

#### Risk 3: Agent Graph is architecturally fractured

**Severity:** HIGH
**Evidence:**
- Production Agent Graph: no integrity key → `storage_class: persisted_unverified`, `terminal_persistence: disabled_without_integrity_key`, no durable resume, no checkpointing.
- Staged candidate (v0.2.5): keyed daemon works, proxy fixed, 145+ tests pass, restart-verified — BUT: 27 clippy/MSRV findings, no production install, no hostile review.
- Default model `glm-5.2:cloud` is unreachable through Ollama → all LLM-node graphs fail.
- The plan lists Agent Graph as a required service but doesn't specify which version, which data directory, which key, or which model.

**Consequence:** The orchestration layer the plan depends on is split across a broken production instance and a qualified-but-uninstalled staging candidate. Neither is production-ready.

**Fix:** Either install the staged candidate with integrity key into production (after clippy resolution) OR formally accept the production instance's limitations and remove graph-orchestrated workflows from scope. The current split-state is untenable.

#### Risk 4: Source preservation is incomplete and Libraries is dangerous

**Severity:** HIGH
**Evidence:**
- 90 of 93 repositories classified as needing backup.
- The existing restic snapshot predates the classification and does not include post-classification work.
- `Libraries` repo: 389 dirty entries, 2,421 unknown ignored entries, submodule-status-error, head-not-exactly-remote.
- The Libraries repo contains agent-graph-mcp source, semantic-memory, and other critical components. It cannot be safely modified.

**Consequence:** A format-and-restore cycle could lose uncommitted work across dozens of repositories. The Libraries repo in particular is a minefield — any automated cleanup could destroy important state.

**Fix:** Create a fresh preservation snapshot covering all 90 repos. For Libraries specifically: preserve via `git bundle` + working-tree tarball without attempting cleanup. Do not touch Libraries until a verified preservation snapshot exists.

#### Risk 5: No hardware qualification exists for the target

**Severity:** MEDIUM (release-blocking)
**Evidence:**
- 15 observed rtw89 firmware crashes on current Nobara.
- Zero Fedora live-boot sessions on this laptop.
- Zero suspend/resume cycles tested.
- Zero Wi-Fi soak tests performed.
- No battery/thermal measurements exist.

**Consequence:** The plan may be targeting hardware that cannot run Fedora 44 reliably. The Wi-Fi crash is already a known issue on the current OS — Fedora's kernel/firmware may behave identically or worse.

**Fix:** Boot a verified Fedora 44 live USB (read-only, no install) and run the hardware qualification suite described in P5. This is non-destructive and provides the single highest-ROI evidence before any build work.

### Plan section gaps

| Plan Section | Verdict | Gap |
|---|---|---|
| §1 Verdict | ADEQUATE | Correctly states NO-GO. The "guarantee" definition is realistic. |
| §2 Authority | ADEQUATE | Hierarchy is correct, corrections table is accurate. |
| §3 Locked decisions | ADEQUATE | Comprehensive. Missing: explicit decision on Agent Graph version/configuration. |
| §4 Ownership map | GAP | Lists canonical owners but provides zero verification that current Nobara matches. No migration test plan. |
| §5 Dependency graph | GAP | Serialization rules are correct but no phase has been started. The graph is a plan for a plan. |
| §6 P0 Source freeze | GAP | Evidence root not created. 90 repos not preserved. Libraries dangerous. |
| §7 P1 Backup/restore | GAP | check passed, restore not done, off-device not done. P1 requirements list the right things but zero are complete. |
| §8 P2 Build | GAP | Nothing built. Manifest exists but no actual build run. |
| §9 P3 VM matrix | GAP | Zero VMs. The matrix design is thorough but unexercised. |
| §10 P4 Stack E2E | GAP | Zero tests. |
| §11 P5 Hardware | GAP | Zero qualification. Wi-Fi crash is acknowledged but not tested. |
| §12 P6 Recovery media | GAP | No media created or booted. |
| §13 Gate F | GAP | The gate checklist is correct but every item is unchecked. The residual risks section is honest. |
| §14 P7 Migration | SPECULATIVE | Entirely dependent on all prior phases. |
| §15 P8 Burn-in | SPECULATIVE | Dependent on P7. |
| §16 Feature ROI | ADEQUATE | Tier classification is sensible. Tier 3 correctly defers experiments. |
| §17 Receipt format | ADEQUATE | The receipt schema is well-designed. |

### Missing gates the plan should include

1. **Agent Graph integrity key gate** — Production Agent Graph has no key. The plan mentions Agent Graph as a required service but never specifies key configuration or version pinning.
2. **clippy/MSRV gate** — The staged candidate has 27 clippy findings. Any build system should fail on warnings.
3. **Libraries repo safety gate** — The plan never acknowledges that Libraries is heavily dirty and dangerous to modify.
4. **Model availability gate** — The plan assumes LLM orchestration works but the default model is unreachable.
5. **Ollama dependency gate** — The plan says "Candle is final owner" but the current stack depends entirely on Ollama. No migration test exists.
6. **Chrome profile migration gate** — Separate personal/automation profiles are specified but no migration test from current shared state exists.

## 2. Hostile Review

### Claims adjudicated

| Claim | Verdict | Evidence |
|---|---|---|
| Fedora 44 KDE will install on this hardware | UNVERIFIED | No live boot, no VM with this exact hardware config, Wi-Fi firmware already crashes |
| Candle will replace Ollama | UNVERIFIED | Candle mmap confirmed but no service exists, cross-process sharing not measured, zero migration work done |
| LUKS2 passphrase recovery is sufficient | UNVERIFIED | No recovery rehearsal, no secondary keyslot tested, no live-media unlock practiced |
| 20 suspend/resume cycles will pass | UNVERIFIED | Zero cycles tested, Wi-Fi firmware unstable |
| 90 repos can be preserved | UNVERIFIED | No preservation snapshot exists, classification post-dates backup |
| All services will have one owner | UNVERIFIED | Current Nobara has undocumented ownership; no clean migration test |
| The plan covers all failure modes | FALSE | No failure-injection tests; installer-interruption, power-loss-during-format, and bitlocker-recovery-loop scenarios are untested |
| Pre-format gates are well-defined | PARTIALLY TRUE | Gate F checklist is thorough but omits Agent Graph key, clippy, Libraries safety, and model availability |
| External HDD is backup-only | VERIFIED | User decision recorded; no repartitioning occurred; plan respects this |
| restic repository integrity | VERIFIED | check --read-data passed 1848/1848 packs, no errors |
| Agent Graph staged build passes tests | VERIFIED | 145+ tests pass, 3 new transport regression tests, restart persistence confirmed |
| Source classification complete | VERIFIED | 93 repos examined, receipt at receipts/preformat/00-source-freeze-git.json |

### Unsafe assumptions

1. **"The plan can be executed in sequence."** The plan has 8 phases, zero of which have started. Each phase depends on the prior. The total effort is weeks, not days. The plan is a specification, not a schedule.

2. **"Existing services will migrate cleanly."** Seven recurring services run on Nobara. The plan assumes they'll map cleanly to Fedora 44 systemd units. No migration has been tested.

3. **"Windows dual-boot is straightforward."** Windows-first installation with BitLocker, Fedora LUKS, shared ESP, and UEFI boot entries interacting correctly has never been rehearsed — not even in a VM.

4. **"The Wi-Fi will work or an adapter is acceptable."** The user's budget is $900/month. A USB Wi-Fi adapter is a workaround, not a solution. The Realtek crash may affect any distro using the same firmware.

5. **"Agent Graph will be ready when needed."** The production instance is broken for LLM workloads. The staged fix isn't installed. No decision has been made on which to use.

### GO/NO-GO recommendation

**Verdict: NO-GO**

The plan is well-structured as a design contract. It identifies the right phases, the right gates, and the right safety boundaries. But it is a plan, not evidence. Every phase from P0 through P8 is aspirational.

**Conditions that must be met before GO:**

1. Full clean-destination restore verified (P1 complete)
2. Off-device backup exists and a sample downloaded successfully (P1 complete)
3. All 90 repos preserved in a current snapshot (P0 complete)
4. Agent Graph production instance either fixed (key + model) or formally replaced with staged candidate (decision made)
5. Fedora 44 live USB booted on this laptop, Wi-Fi soak passed or explicit workaround accepted (P5 hardware qualified)
6. At least one clean VM install from an actual build artifact (P3 started)
7. Recovery secrets proven retrievable outside laptop

**Formatting remains forbidden until Gate F checklist is fully checked with current receipts.**

## 3. Receipts referenced

- `receipts/preformat/00-source-freeze-git.json` — source classification
- `receipts/preformat/01-restic-full-data-check.json` — full data check passed
- `receipts/preformat/02-agent-graph-daemon-create-smoke.json` — staged daemon create smoke
- `receipts/preformat/03-agent-graph-daemon-restart-smoke.json` — staged daemon restart persistence
- `receipts/preformat/AG-LLM-QUARANTINE.md` — Agent Graph LLM quarantine
- `docs/ULTIMATE-IMPLEMENTATION-PLAN-v1.0.md` — canonical plan
