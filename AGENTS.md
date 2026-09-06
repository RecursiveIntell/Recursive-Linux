# AGENTS.md — Hermes Workbench OS

## Mission
Build and qualify a reproducible, encrypted Fedora-based workstation centered on Hermes Desktop, Chrome, Josh's active control-plane stack, and isolated experimental profiles.

## Source hierarchy
1. Current live host and attached-device evidence.
2. This repository's admitted contracts and receipts.
3. Current Fedora, kernel, systemd, Chrome, Hermes, and hardware primary documentation.
4. User-approved decisions in the active task.
5. Prior conversation and memory only as historical context.

## Hard safety rules
- Do not erase, repartition, format, install a bootloader, modify UEFI variables, enroll Secure Boot keys, or overwrite an external device without an explicit device-identity receipt and user approval at that gate.
- Nobara remains the rollback environment until Google Drive backup, restore sampling, external Workbench qualification, and Windows-media readiness all pass.
- Never place credentials, OAuth tokens, browser cookies, SSH private keys, `.env` secrets, or recovery keys in this repository or an installer image.
- Google Drive upload success is not backup closure. Require a local manifest, remote inventory, size/count reconciliation, hashes where practical, and sampled restore verification.
- Keep the stock Fedora kernel installed and bootable. Experimental kernels or eBPF/sched_ext policies are optional candidates with bounded rollback.
- Do not silently broaden backup, network, privilege, or service scope.
- Do not commit or push until controller verification is complete.

## Architecture invariants
- Fedora 44 conventional minimal host for v1; bootc remains an evaluated v2, not assumed production truth.
- KDE Plasma Wayland practical-minimal session; XWayland retained for automation compatibility.
- Personal Chrome and Automation Chrome use separate profiles.
- Semantic memory has one heavyweight owner; sessions use thin clients/proxies.
- Host services, developer toolchains, persistent state, caches, and secrets are separate layers.
- SELinux remains enforcing; firewalld is default deny inbound; Tailscale is the preferred remote plane.
- Expensive/risky workloads are activated through explicit profiles, not all started at login.

## Required evidence states
Use: proposed, source-present, build-verified, VM-verified, external-media-verified, restore-verified, dual-boot-verified, blocked, or quarantined. Never collapse these into "done."

## Completion
A phase closes only with changed files, commands run, checks passed/failed/skipped, unresolved risks, rollback steps, and an auditor-rerunnable receipt.
