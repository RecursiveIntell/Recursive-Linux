# Pre-Format GO/NO-GO Verdict

**Evidence cutoff:** 2026-09-06
**Target:** current HP laptop and any future Fedora Workbench migration
**Verdict:** **NO-GO — do not format, repartition, write installer media, or migrate the internal disk**

## Current verified evidence

### Foundation and protected workflows

- Protected availability check passes 10/10.
- PAIR compatibility ingress and the loopback Ollama engine have distinct, functioning port ownership.
- A real embedding request succeeded through the routing boundary.
- Mnemes fact-create synchronization recovered under explicitly approved namespace admissions; the verified laptop/replica stream reached matching sequence and digest state.
- Screenshot capture and save were exercised with a real output image.

### Recovery evidence

- Existing encrypted restic repository: full pack-data read passed before the current snapshot (`1848/1848`, no errors).
- Current SQLite staging: 152/152 selected databases have integrity-checked online backups. Chrome was shut down only after operator confirmation and was relaunched after staging.
- Current encrypted snapshot: completed and read back from the repository.
- Three critical staged databases—including Ares state plus Chrome login/history state—were streamed from the new snapshot and matched their staged SHA-256 digests.
- A 5.88 GiB isolated sample restore passed content hashes, modes, a symlink target, a Unicode path, a file larger than 1 GiB, SQLite integrity, restored DevKit help execution, and a non-empty semantic-memory HTTP search against the restored copy.
- Full metadata-faithful restore into a 150 GiB disposable Fedora VM is the active next recovery gate.

### Source and installer evidence

- Local project validation and 20 unit tests pass.
- Fedora 44 `ksvalidator` passes both Kickstart files in an ephemeral Fedora 44 container.
- Every package/group in the host manifest resolves from Fedora 44 repositories.
- Official Fedora 44 netinstall and KDE media passed OpenPGP-backed checksum validation.
- A disposable UEFI/Q35/KVM install completed; qcow2 integrity passed; the installed Fedora 44 guest booted to a serial login prompt with SELinux enforcing, firewalld, SSH, and zram active.
- The old hardware writer has been replaced by a tested hard-stop quarantine wrapper. It contains no device-selection variable, VM Kickstart reference, or block-device write command.

## Blocking gates

1. **Independent recovery password:** the restic password has no tested copy outside this laptop. Instructions exist locally; the operator must perform the off-laptop storage and retrieval test without exposing the password to the agent.
2. **Full restore:** the complete current snapshot must finish restoration onto an isolated Linux filesystem and pass count, type, metadata, database, and application-level checks.
3. **Off-device independence:** the attached external disk is a separate device but not an independently located copy. Cloud or a second offline medium remains unverified.
4. **Versioned source:** the repository has been initialized locally but has no initial commit or remote. A narrow initial source-snapshot commit requires private-receipt exclusion, sanitized evidence, current status wording, controller verification, and public-evidence review.
5. **VM matrix:** one install is evidence, not the required repeated installs, disk variants, network/failure injection, update/reboot, and rollback matrix.
6. **Hardware qualification:** no current non-destructive live-media Wi-Fi, suspend/resume, graphics, audio, peripheral, and thermal qualification receipt exists for this exact candidate.
7. **Recovery media and dual boot:** Windows recovery media, firmware boot rehearsal, partition plan, and dual-boot update/rollback remain unverified.
8. **Architecture decision:** the historical Candle-only inference target conflicts with the functioning PAIR/Ollama owner boundary. No installer may silently choose between them.
9. **Exact-device approval:** no approval names a physical target, partition plan, or media write. Generic instructions to finish the plan do not satisfy that gate.

## Current live/target differences

- Current Nobara root: Btrfs with zstd, no LUKS, SELinux disabled.
- Fedora production target: encrypted storage and SELinux enforcing.
- Current power owner: TLP. No second power controller may be layered on without measured comparison and explicit replacement.
- Current boot manager: GRUB; existing firmware entries include multiple operating systems and must not be altered by this phase.

## Allowed next work

- Complete the disposable full restore and verification.
- Finish the sanitized source receipt and private/public file boundary.
- Run additional disposable VM trials and failure injections.
- Run workload and power measurements only after recovery/VM background I/O ends.
- Prepare non-destructive live-media qualification and exact-device receipts.

## Forbidden until all gates pass

- `mkfs`, partition-table changes, block-device writes, bootloader installation, UEFI mutation, Secure Boot enrollment, backup pruning, remote deletion, internal-disk migration, or promotion of the VM credential/artifact to hardware use.

## Next decision

Remain **NO-GO** until the independent password, full restore, source identity, VM matrix, hardware qualification, recovery-media, and exact-device approval gates all pass. A later GO receipt cannot itself authorize a hardware write; that remains a separate operator action.
