# Google Drive backup and restore verification

**Evidence state: proposed / preflighted — not uploaded, not restore-verified.**
**Host:** Nobara Linux, kernel `7.1.3-200.nobara.fc44.x86_64` (reported by task context).
**Scope:** canonical personal data before any erase. This document deliberately contains no credentials, tokens, cookies, keyring data, or secret contents.

## 1. Safety boundary and closure gate

This is a plan, not proof of backup completion. Do not erase Nobara until all of these are true:

1. A local, immutable-in-practice manifest and command receipt exists outside the data being erased.
2. Remote inventory reconciles with the manifest by path, count, and byte size; hashes match where the backend exposes them.
3. A sampled restore to a new local directory succeeds, including opening representative documents/media and restoring at least one project file.
4. The sample includes a large file, a sparse file, a Unicode/long-name path, a symlink-policy case, and live-state exports made by application-aware methods.
5. A second copy or rollback environment remains available. Google Drive upload success alone is not closure.

No upload, authentication, installation, deletion, compression, source-tree modification, or system-configuration change was performed during this preflight.

## 2. Observed preflight evidence

Commands were read-only and run from `/home/sikmindz` unless stated otherwise:

- `df -h /home/sikmindz` reported a 458G filesystem, 287G used, 167G available (64%).
- `rclone`, `google-drive-ocamlfuse`, and `gdrive` are absent. Homebrew and `gog` exist at `/home/linuxbrew/.linuxbrew/bin/`, but `gog` has no configured/authenticated Drive remote per the supplied current facts. No mount containing `drive` or `google` was found with `findmnt`.
- `du -x -d1 -h /home/sikmindz` reported approximately: `Coding` 73G, `.hermes` 20G, `.cache` 15G, `.local` 63G, `Downloads` 7.2G, `Documents` 1.6G, `Videos` 872M. These are estimates and must be re-measured at execution time.
- `Coding` contains roughly 759,510 files, 130,917 directories, 830 symlinks, and 450 sparse files. It contains many Git worktrees/repositories and build outputs.
- `.hermes` contains roughly 155,392 files, 13,683 directories, 125 symlinks, and 125 sparse files. `.hermes/state.db` is a sparse ~4.8GB logical-size database; it must not be treated as an ordinary static file while active.
- `.config`, `.local/share`, `.mozilla`, and `.hermes` contain active application state and database/WAL material. `.config` includes Google Chrome and gcloud paths; browser profiles and credentials are sensitive and must not be copied wholesale.
- The requested repository exists at `/home/sikmindz/Projects/hermes-workbench-os`, but no `.git` metadata was present in that directory during this check. Only this document may be written for this task.

The counts and sizes are evidence of topology only, not a backup inventory. Re-run them immediately before the real operation.

## 3. Data classification and default scope

### Canonical / back up by default

- `~/Documents`, `~/Pictures`, `~/Videos`.
- `~/Coding` source, design notes, datasets explicitly identified as personal/canonical, Git metadata, and dirty worktree changes. Preserve repository-relative paths and symlink policy.
- `~/Downloads` only after a human review: retain personal documents, installers needed for recovery, and irreplaceable artifacts; exclude reproducible downloads, caches, and duplicate media.
- Selected Hermes state needed for continuity, preferably application exports and databases made consistent by an application-aware procedure. Include configuration only after redaction review.
- A reviewed subset of `~/Projects`, `~/projects`, `~/Markdown`, `~/My Stuff`, and other personal top-level directories. The many home-level project/build trees make an unreviewed `$HOME` backup unsafe and likely too large.

### Reproducible / normally exclude

Build directories (`target`, `node_modules`, `.venv`, `.gradle`, Android SDK/tool caches, compiler outputs), package caches, model caches whose sources are known, `~/.cache`, temporary files, browser caches, and generated benchmark outputs. Record exclusions in the manifest so they are intentional rather than silently missing.

### Sensitive / quarantine unless explicitly approved

Never upload: `.env*`, SSH/GPG private keys and keyrings (`~/.ssh`, `~/.gnupg`, `~/.pki`), cloud credentials and tokens (`~/.config/gcloud/credentials.db`, `access_tokens.db`, account/keyring stores), browser cookies/session databases (`~/.config/google-chrome`, Firefox profile cookies, and equivalent profiles), recovery codes, password stores, and private signing material. Do not even hash or print their contents. If browser continuity is needed, export bookmarks/passwords through the browser's own controlled UI; passwords should use a separate password-manager export and separate encryption decision, not Drive plaintext.

## 4. Symlinks, sparse files, Git, and live databases

- Use an explicit symlink policy. Safer default: archive the link itself only when the target remains inside an included root; never follow links outside the selected roots. Produce a review list of dangling and external links.
- Preserve sparse allocation where the chosen transfer path supports it, but reconcile **logical size and content hash**, not filesystem blocks. Do not convert a sparse database or VM image to a dense copy without checking free space.
- For every Git repository: capture `git status --short`, current branch/HEAD, and uncommitted diff metadata into the local manifest (without reading secrets). Back up `.git` and dirty files if the repository is canonical. A remote Git hosting copy is not a substitute for unpushed work.
- Do not copy SQLite files by ordinary recursive copy while applications are running. Close the owning application and copy the database plus `-wal`/`-shm` as a consistent set, or use `sqlite3 DB ".backup 'export.db'"` (or the application's documented export) to a staging path. Verify the backup with `PRAGMA integrity_check;` on the staged copy. For `.hermes` and semantic-memory databases, prefer documented Hermes exports/snapshots; never upload live session stores or credentials by default.
- Stop Chrome/Firefox before any explicitly approved bookmark/profile export. Do not back up live browser profiles wholesale.

## 5. Recommended design: rclone plus optional crypt

Install and configure only after user approval at the installation/authentication gate. Recommended layers:

1. **Local staging/manifest:** build a reviewed include/exclude list; write a manifest outside the source roots containing relative path, type, logical byte size, mtime, symlink target (if applicable), and SHA-256 for practical-size files. Hash very large files in a throttled pass; record `hash_skipped` with a reason rather than pretending verification.
2. **Drive remote:** configure an rclone `drive` remote interactively. The user must select the intended Google account, consent in a browser, and confirm the target Drive folder and available quota. The agent must not receive or print OAuth material.
3. **Privacy choice:** prefer an rclone `crypt` remote layered over Drive. The user creates and retains the crypt password/salt independently; do not put it in shell history, this repository, logs, or the backup manifest. Plain Drive is acceptable only for data already classified public/non-sensitive and only with explicit approval.
4. **Transfer:** use `rclone copy`, never `sync`, for the first backup. Use a new dated root such as `Nobara-pre-erase-YYYYMMDD`; `copy` avoids remote deletion. Use conservative `--transfers`, `--checkers`, bandwidth limits, retries, and a log path outside sensitive roots. Include `--dry-run` first and inspect the file list.
5. **Reconciliation:** run `rclone check SOURCE REMOTE --size-only` initially, then `rclone check --download` for a bounded/high-value sample. On a crypt remote, remote hashes are not available in the same way; rely on local manifest hashes plus downloaded-content hashes. Do not interpret a successful listing as content verification.

Illustrative commands (do not run during preflight; replace placeholders only after review):

```bash
# After rclone is installed and the user authenticates interactively:
rclone config                 # create drive: and, preferably, crypt: over it
rclone copy --dry-run /stage/ Nobara-pre-erase-YYYYMMDD: --exclude-from /stage/excludes.txt
rclone copy /stage/ Nobara-pre-erase-YYYYMMDD: \
  --exclude-from /stage/excludes.txt --transfers 2 --checkers 4 \
  --retries 8 --low-level-retries 20 --log-file /stage/rclone-copy.log
rclone check /stage/ Nobara-pre-erase-YYYYMMDD: --one-way --size-only \
  --missing-on-dst /stage/missing.txt --differ /stage/differ.txt
```

For large roots, stage each class separately (`canonical-docs`, `source`, `media`, `approved-state`) so a quota or retry failure cannot obscure which class completed. Do not compress everything into one opaque archive: it defeats incremental reconciliation and sampled per-file restore. If a single file approaches Drive's current per-file limit, split only with a documented, tested format and retain the recovery tool; otherwise exclude and flag it.

## 6. Manifest and remote inventory contract

Store (outside the erase target) at least:

- UTC start/end time, hostname, filesystem/device identity, tool versions, exact source roots, exclusions, symlink policy, sparse-file policy, and crypt/plain mode.
- For each included object: normalized relative path, type, logical size, mtime, SHA-256 or explicit skip/error state.
- For each excluded class: rule, estimated size, and human approval/review status.
- rclone dry-run output, transfer log, final `rclone size`/listing, `rclone check` outputs, and the Drive folder ID/name chosen by the user (folder ID is not a secret but do not disclose auth config).
- A generated inventory digest (SHA-256 of the manifest) and a signed/printed receipt kept on a second local medium if available.

Use UTF-8/NFC normalization consistently, detect path collisions after normalization, flag control characters and excessively long components, and test problematic names in the dry run. Google Drive's API documents a maximum individual upload size of 5,120 GB; practical account quota, daily upload limits, network reliability, and rclone/backend behavior remain gating constraints. Check current Drive quota/limits immediately before transfer rather than relying on stale estimates. References: [Drive upload guide](https://developers.google.com/drive/api/guides/manage-uploads), [Drive limits](https://developers.google.com/workspace/drive/api/guides/limits), [rclone Drive](https://rclone.org/drive/), [rclone check](https://rclone.org/commands/rclone_check/), and [rclone crypt](https://rclone.org/crypt/).

## 7. Restore verification before erase

1. Create a fresh, empty restore directory on a filesystem with sufficient space; never restore over the live home.
2. Restore a stratified sample: at least 20 files from each canonical class, one file >1GB, one sparse file, one Unicode/long-name path, one symlink case, several dirty Git files, one document from each important format, and representative photos/videos.
3. Hash restored files against the local manifest where plaintext is available. For crypt, decrypt through rclone and hash the restored plaintext; do not compare encrypted object hashes.
4. Run `git diff --no-index` or equivalent against staged copies for selected source files; open/read representative documents and play/inspect representative media.
5. Validate staged SQLite exports with `sqlite3 ... 'PRAGMA integrity_check;'` and record the result. Do not test by opening the live DB in place.
6. Confirm permissions/ownership only as a documented expectation; avoid restoring executable bits or special files unless explicitly needed.
7. Record missing, differing, unreadable, or intentionally excluded objects. Any unexplained difference blocks erase.

## 8. Required user interaction and stop conditions

The user must choose the Google account, Drive destination, plain versus crypt mode, quota/billing plan, reviewed roots/exclusions, and retention policy. They must perform OAuth consent and retain the crypt password/recovery material. Pause for approval before installing rclone, authenticating, staging sensitive state, starting upload, or erasing Nobara.

Stop and quarantine on quota insufficiency, ambiguous account/folder identity, unexpected symlink traversal, active database without a consistent export, any credential/cookie/key discovery in the proposed include set, unexplained `rclone check` differences, or failed restore samples. Keep Nobara bootable until the evidence state is explicitly upgraded to `restore-verified` by a human-reviewed receipt.
