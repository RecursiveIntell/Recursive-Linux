# Hermes Workbench OS

<!-- last-verified: 2026-09-06 -->

Source prototype for a Fedora-based workstation profile targeting reproducible builds, encrypted production storage, KDE Plasma, Hermes Desktop, Chrome, governed local services, remote compute, and isolated experimental workflows.

## Current evidence state

**NO-GO for hardware installation, formatting, repartitioning, or migration.**

Verified locally at the 2026-09-06 evidence cutoff:

- project validator passes;
- 20 unit tests pass;
- both Kickstart files pass Fedora 44 `ksvalidator` in an ephemeral Fedora 44 container;
- every item in `manifests/host-packages.txt` resolves from Fedora 44 repositories;
- an official-checksum-verified Fedora 44 netinstall image was used to build a disposable-VM candidate;
- one isolated UEFI/Q35/KVM guest completed installation, its qcow2 passed integrity checks, and the installed Fedora 44 system booted to a serial login prompt;
- the former hardware-media writer is a hard-stop quarantine wrapper and cannot write a device.

Not verified or not complete:

- reproducible double-build output;
- the full multi-install and failure-injection VM matrix;
- external-media installation or live-hardware qualification;
- Windows recovery and dual-boot rehearsal;
- production LUKS2 configuration;
- hardware-media identity and write approval;
- complete pre-format recovery authority, including independently retrievable backup credentials;
- internal-disk migration or production readiness.

A disposable VM pass is not hardware or release certification. Generated images, raw machine receipts, credentials, personal paths, and backup inventories remain private and untracked.

Sanitized evidence:

- [`receipts/public/20260906-source-and-vm-gates.json`](receipts/public/20260906-source-and-vm-gates.json)
- [`receipts/public/20260906-recovery-and-media-gates.json`](receipts/public/20260906-recovery-and-media-gates.json)

## Safety boundary

The source tree never grants authority to modify a physical disk. The production Kickstart remains interactive-safe: it has no disk-clear directive, password, passphrase, boot target, or UEFI mutation. The VM Kickstart is intentionally destructive only toward its isolated virtual disk and contains a public insecure test credential; it must never be used on hardware, a bridged network, or a persistent system.

## Target sequence

1. preserve current source and complete independently usable recovery;
2. version and reproduce the source/build inputs;
3. run the complete disposable VM matrix;
4. perform non-destructive live-media hardware qualification;
5. certify recovery and installer media only after exact-device review;
6. request a separate operator approval for any hardware write or internal migration.

## Default product decisions

- Base: conventional Fedora 44 profile generated from reviewed Kickstart source.
- Desktop: practical-minimal KDE Plasma Wayland with XWayland.
- Production security target: LUKS2, SELinux enforcing, and firewalld; TPM/Secure Boot remain separately gated.
- Browser: separate personal and automation profiles.
- Services: one explicit owner per inference, memory, graph, automation, and power-policy boundary.
- Rollback: the current Nobara installation remains the production baseline until every recovery, VM, hardware, and approval gate passes.

## Repository layout

- `docs/` — architecture, recovery, migration, and runtime decisions
- `kickstart/` — interactive-safe production template and isolated VM fixture
- `manifests/` — package, service, profile, and persistent-state allowlists
- `overlays/` — configuration installed by a future admitted build
- `scripts/` — validation, backup, restore, and fail-closed tooling
- `tests/` — static and behavioral safety checks
- `receipts/public/` — sanitized, non-secret evidence only

See `AGENTS.md` for safety and completion contracts. Current status is summarized in `docs/PREFORMAT-GO-NO-GO.md`.
