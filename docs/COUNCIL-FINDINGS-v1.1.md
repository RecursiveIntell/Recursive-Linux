# Council Findings v1.1 — Agent Graph Executed

**Date:** 2026-07-26
**Produced by:** Agent Graph MCP with `glm-5.2:cloud` (both graphs completed successfully)
**Architecture council run:** `run-19f9f9baca0-c` (68.2s, 4 LLM calls, `hwos-council-v3-glm`)
**Hostile review run:** `run-19f9f9bb2af-d` (65.3s, 4 LLM calls, `hwos-hostile-v3-glm`)
**Previous quarantine:** The earlier failures were caused by model resolution — the old graphs had no explicit `model` field on LLM nodes, and the server default path was not reliably routing to `glm-5.2:cloud`. v3 graphs set `"model": "glm-5.2:cloud"` explicitly on every LLM node. This is now the working pattern.

---

## Architecture Council Report

> **Unified Architecture Report: Hermes Workbench OS v1.0**
>
> **1. Executive Summary**
> The Hermes Workbench OS v1.0 plan outlines a rigorous, 8-phase (P0-P8) deployment strategy targeting a dual-boot Fedora 44 KDE/Plasma environment on an HP Laptop. The architecture relies on conventional Fedora (rather than Kinoite), rootless Podman, SELinux enforcing, and a CPU-only ML stack (Candle/UNO Q). While the architectural blueprint is highly methodical, current execution metrics reveal critical gaps in data protection, hardware validation, and environment staging that must be addressed before migration.
>
> **2. Top 5 Combined Risks (Priority Order)**
>
> **Priority 1: Severe Data Loss Vulnerability**
> - Evidence: Google Drive backup has FAILED. Source classification shows 90 out of 93 repositories require backup, and the Libraries repo contains 389 dirty entries.
> - Recommended Actions: Halt progression to further phases until the Google Drive backup pipeline is fixed and verified. Execute an immediate, comprehensive backup of the 90 unprotected repositories. Clean the 389 dirty entries in the Libraries repo to ensure a reproducible build state.
>
> **Priority 2: Hardware Instability and Wi-Fi Failure**
> - Evidence: The target hardware (HP Laptop 15-fc0xxx) has experienced 15 firmware crashes related to the Realtek RTL8852BE-VT Wi-Fi adapter. No hardware qualification has been performed yet.
> - Recommended Actions: Expedite Phase 6 (Hardware Qualification). Stress-test the Wi-Fi adapter under Fedora 44 to confirm if the crashes persist. If unresolved, procure a Linux-compatible USB Wi-Fi dongle as a fallback and document it in the hardware profile.
>
> **Priority 3: Lack of Pre-Deployment Validation and Recovery**
> - Evidence: There are zero current VM installations. Old VM artifacts have been quarantined. Recovery secrets are not proven retrievable outside the laptop.
> - Recommended Actions: Complete a full clean-destination restore from the verified restic snapshot. Perform a VM installation matrix (3 clean installs, 10 cold boots, LUKS recovery). Verify recovery secrets are accessible from an independent device.
>
> **Priority 4: Agent Graph Fragmentation**
> - Evidence: The production Agent Graph instance lacks an integrity key. The staged v0.2.5 candidate has 27 clippy/MSRV findings. The default model was unreachable in earlier attempts.
> - Recommended Actions: Resolve the 27 clippy/MSRV findings. Install the staged candidate with a configured integrity key into production. Verify the default model is reachable before any graph-dependent phase.
>
> **Priority 5: No Candle Service and Unmeasured Cross-Process Sharing**
> - Evidence: Candle is designated to replace Ollama, but no Candle service exists. Cross-process shared weights are not measured.
> - Recommended Actions: Prototype a single-owner Candle embedding service. Measure RSS, page-cache, and latency under concurrent client load. Do not remove Ollama until Candle is proven.
>
> **Structural Assessment:** The plan is structurally sound and methodical. The phase ordering (P0-P8) is correct. The primary weakness is execution — every phase is aspirational. The plan is a design contract, not evidence of readiness.

---

## Hostile Review — Chief Judge's Verdict

> **CHIEF JUDGE'S FINAL VERDICT**
>
> **VERDICT: NO-GO**
>
> The Hermes Workbench OS v1.0 implementation plan is hereby rejected for execution. The evidence demonstrates catastrophic gaps in data safety, hardware validation, and software readiness. Proceeding with the P0-P8 phases under current conditions poses an unacceptable risk of permanent data loss and system bricking.
>
> **UNRESOLVED CRITICAL FINDINGS:**
>
> 1. Data Loss Risk (No Off-Device Backup): There is no off-device backup. The primary restic check passed locally, but Google Drive FAILED. A local-only backup on a machine about to undergo a destructive dual-boot installation and LUKS2 formatting is a single point of failure.
> 2. Environment Instability (Dirty Libraries): 389 dirty library entries exist in the current environment. This guarantees a corrupted or unstable baseline for the new OS.
> 3. Hardware Reliability Unproven (Wi-Fi & Suspend): The target hardware has 15 known firmware crashes, and zero suspend/resume cycles have been tested. Proceeding without hardware qualification will result in an unusable system.
> 4. Recovery Key Failure (LUKS2 Secrets): Recovery secrets are not proven to work outside the laptop. If the OS install fails and the bootloader is corrupted, the data will be permanently unrecoverable.
>
> **UNRESOLVED HIGH FINDINGS:**
>
> 1. Clean Install Unverified: No live qualification has been done for Fedora 44 KDE Plasma Wayland on the target hardware.
> 2. Core Component Non-Existent: Candle is claimed to replace Ollama, but no Candle service exists, and cross-process sharing is unmeasured.
> 3. Data Classification Mismatch: 90 repos are claimed to be preserved, but no snapshot exists, and the backup predates the classification.
> 4. Agent Graph Not Production-Ready: 27 clippy/MSRV findings. No integrity key in production. Default model was unreachable in earlier attempts.
> 5. No Failure Injection Testing: The plan claims to cover all failure modes, but no failure-injection tests, Windows-preservation rehearsal, or installer-interruption recovery tests exist.
>
> **CONDITIONS FOR GO:**
>
> 1. Fix Google Drive backup and verify off-device data integrity.
> 2. Clean Libraries repo dirty entries and create a comprehensive source preservation snapshot.
> 3. Boot Fedora 44 live USB on the target laptop and pass Wi-Fi soak + 20 suspend/resume cycles.
> 4. Perform full clean-destination restore and validate all databases.
> 5. Verify recovery secrets are accessible from an independent device.
> 6. Complete at least one clean VM install from an actual build artifact.
> 7. Resolve Agent Graph clippy/MSRV findings and install with integrity key.

---

## Council consensus

Both councils independently arrived at the same verdict: **NO-GO**. The architecture council found the plan structurally sound but aspirational. The hostile review found catastrophic gaps in data safety, hardware validation, and software readiness.

Both agree on the same top priorities:
1. Off-device backup and full restore verification
2. Hardware qualification (Wi-Fi + suspend/resume)
3. Source preservation (90 repos + Libraries cleanup)
4. Recovery secret verification
5. Agent Graph production readiness

## Receipts

- `receipts/preformat/04-architecture-council-v3.json` — architecture council full output
- `receipts/preformat/05-hostile-review-v3.json` — hostile review full output
- `receipts/preformat/AG-LLM-QUARANTINE.md` — earlier failures documented (now resolved by explicit model field)