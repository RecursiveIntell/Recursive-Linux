# Recovery and Migration Runbook

## Absolute stop conditions

Stop before disk mutation if any condition is true:

- the Google Drive backup receipt or sampled restore receipt is not passing;
- the restic recovery password is available only on this laptop;
- the selected device does not match a fresh stable-device identity receipt;
- Windows/Fedora recovery media or BitLocker/LUKS recovery material is unavailable;
- the external Workbench stock-kernel boot has not passed hardware acceptance;
- internal power is not connected or the Wi-Fi/storage path is unstable.

## 1. Current rollback

Nobara is the live rollback environment. Do not remove its boot entry or partitions during the external-media phase. Record:

```bash
lsblk -e7 -o NAME,PATH,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL,TRAN
findmnt --real --output TARGET,SOURCE,FSTYPE,OPTIONS
efibootmgr -v
```

These commands are evidence only; they do not authorize mutation.

## 2. Backup recovery

Prerequisites:

- rclone Drive OAuth configuration;
- restic repository path receipt;
- restic password held in the desktop keyring **and** a separate password manager/offline record;
- `restic check --read-data-subset=5%` pass;
- deterministic `restic dump --no-cache` sample hash pass.

Recovery on a clean Linux environment:

1. install the receipt-pinned rclone/restic versions or newer compatible versions;
2. recreate the least-authority `gdrive` remote through OAuth;
3. retrieve the restic password outside the failed laptop;
4. run `restic snapshots` and `restic check`;
5. restore into a new empty directory, never over a live home;
6. verify SQLite receipt hashes and `PRAGMA integrity_check`;
7. restore code/personal data first; restore browser/keyring state only after review.

## 3. External-HDD rollback

The external installation must have its own EFI System Partition and boot entry. If it fails:

1. power off;
2. disconnect the external HDD;
3. boot Nobara from the firmware menu;
4. preserve Workbench logs and receipts before reformatting anything;
5. boot the stock Fedora kernel if only an experimental kernel failed.

Never make the external disk's bootloader the sole route to the internal OS.

## 4. Runtime/kernel rollback

- Keep at least two stock Fedora kernels installed.
- Every custom kernel uses a unique package release and boot-menu title.
- `sched_ext` policies must be unloadable; fallback is the stock scheduler.
- The PSI governor can be disabled with:

```bash
systemctl --user disable --now hermes-pressure-governor.service
```

- A Wi-Fi recovery module/backport is quarantined if it creates a firmware reset, suspend regression, or stock-kernel incompatibility.
- TPM auto-unlock is additive. The LUKS recovery passphrase is never removed.

## 5. Windows + Workbench internal migration

This phase requires a fresh explicit erase approval.

1. verify backup and external Workbench receipts;
2. create and boot-test Windows and Fedora installers;
3. record firmware mode and restore default Secure Boot settings if required by Windows;
4. erase/reinstall Windows first;
5. allow Windows to create its required GPT partitions;
6. shrink Windows using Windows Disk Management;
7. install Workbench only into the resulting free space;
8. do not `clearpart --all`; preserve Microsoft partitions;
9. confirm both firmware boot entries independently;
10. enable BitLocker only after both OSes boot repeatedly and its recovery key is external;
11. enable TPM-bound LUKS/Secure Boot only after Linux recovery is rehearsed.

## 6. Minimum post-recovery acceptance

- three cold boots per OS;
- five suspend/resume cycles in Workbench;
- 60-minute Wi-Fi transfer/idle/roam soak with zero firmware resets;
- Chrome Personal and Chrome Automation isolation;
- Hermes conversation, CUA click/type/readback and one Agent Graph receipt;
- semantic-memory integrity/search fixture;
- Tailscale remote path and inbound firewall review;
- Fedora update plus stock-kernel rollback;
- one fresh cloud backup and sampled restore from Workbench.
