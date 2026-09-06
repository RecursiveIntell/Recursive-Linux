# Build and Installation Workflow

## Phase 0 — local source gates

```bash
python3 scripts/validate_project.py
python3 -m unittest discover -s tests -v
```

Fedora-specific gate:

```bash
podman run --rm --security-opt label=disable \
  -v "$PWD:/src:ro" registry.fedoraproject.org/fedora:44 \
  bash -lc '<install pykickstart/dnf tools; validate Kickstart and every package>'
```

A package name from Nobara/Homebrew is not accepted merely because it exists on the live host.

## Phase 1 — backup

1. stage live SQLite stores through `scripts/stage_sqlite_backups.py`;
2. authenticate a least-authority rclone Drive remote;
3. verify quota with `scripts/run_backup.py preflight`;
4. store the restic password in Secret Service and separately off-device;
5. run the fail-closed GitHub coverage classifier;
6. run `scripts/run_backup.py backup --init` for the admitted new repository;
7. run `scripts/run_backup.py verify`;
8. inspect all receipts before accepting G1.

## Phase 2 — build payload

`assemble_payload.py` builds an unprivileged rootfs overlay and content manifest. The Kickstart, package manifest, overlay manifest and Fedora media digest form the installer source identity.

The production Kickstart remains interactive-safe: it intentionally cannot clear or select a disk. A generated device-bound installer is created only after external-media approval.

## Phase 3 — VM

- create a disposable qcow2;
- render a VM-only Kickstart that may clear **only `vda`**;
- boot with UEFI firmware when available;
- install, boot, run static/unit/service gates, update, reboot and test stock-kernel rollback;
- destroy only the recorded qcow2 after receipt preservation.

A VM pass does not prove Wi-Fi, suspend, touch, battery, audio or USB behavior.

## Phase 4 — external HDD

1. connect only the intended external HDD if possible;
2. run `media_preflight.py` and inspect stable identity, size, transport and root-disk exclusion;
3. obtain explicit approval referencing that receipt;
4. install with a distinct EFI partition and LUKS2 passphrase;
5. qualify stock Fedora before activating custom runtime candidates.

## Phase 5 — internal dual boot

Follow `RECOVERY-RUNBOOK.md`. The repository must never contain a generic unattended Kickstart capable of clearing the internal disk.

## Evidence states

- source-present
- static-verified
- Fedora-package-verified
- VM-installed
- VM-boot-verified
- external-media-verified
- hardware-verified
- restore-verified
- dual-boot-verified

Only the highest directly reproduced state may be reported.
