# Hermes Workbench OS: Kernel and Runtime ROI Design

**Status:** design/preflight only; read-only inspection; no package, service, kernel, UEFI, or disk changes.

## Decision in one page

The Workbench should ship the **stock Fedora kernel and upstream interfaces first**. The measurable bottleneck is not a missing scheduler invention: it is duplicated semantic-memory workers, a Realtek firmware failure that persists despite current driver power mitigations, and the absence of a memory-pressure policy. The high-ROI sequence is:

1. **Single-owner semantic memory + explicit cgroup/systemd resource policy** — highest immediate ROI.
2. **PSI/cgroup telemetry and bounded `systemd-oomd` policy** — high leverage, reversible, but only after policy tests.
3. **Retain and tune zram/MGLRU using measurements** — likely useful on a 14 GiB machine; no custom patch.
4. **eBPF observability first; egress enforcement only as a narrowly scoped, tested profile** — useful for auditability, not a default novelty feature.
5. **Wi-Fi mitigation/backport evaluation** — urgent reliability work, but a custom kernel patch is not yet justified; firmware/driver/kernel A-B testing comes first.
6. **UKI, measured boot, Secure Boot admission** — security/reproducibility work for the qualified image, not a performance feature and blocked until backup/VM/external qualification gates pass.
7. **sched_ext** — keep available, but do not make it the default. A custom scheduler earns inclusion only if a controlled benchmark beats stock without harming interactive latency, battery, suspend, or recovery.

**Reject:** a bespoke scheduler, custom memory reclaim algorithm, custom AMD power governor, and kernel-level application policy that duplicates cgroups/systemd/eBPF. These add maintenance and rollback risk without a demonstrated workload delta.

## Evidence boundaries

- **Observed (live host):** current system is Nobara 43, kernel `7.1.3-200.nobara.fc44.x86_64`; HP 15-fc0xxx, SKU B8LA8UA#ABA, Ryzen 7 7730U, AMDGPU, Realtek RTL8852BE-VT using `rtw89_8852bte`; Secure Boot disabled, TPM2 present, GRUB active, no measured UKI reported.
- **Observed:** 14 GiB RAM, 20 GiB swap total, `/dev/zram0` is 3.7 GiB zstd with 693.6 MiB data / 498.7 MiB compressed; current PSI was low but non-zero (`memory full avg60=0.02`, `io some avg60=0.07`). These are a snapshot, not a workload benchmark.
- **Observed:** `systemd-oomd` is inactive. `sched_ext` is compiled in but currently disabled (`state=disabled`, `nr_rejected=0`); `scx_loader` is active only as a DBus loader.
- **Observed:** kernel has `CONFIG_SCHED_CLASS_EXT`, PSI, cgroups, BPF/BPF_LSM/cgroup-BPF, `CONFIG_LRU_GEN_ENABLED`, and zram zstd support. This is sufficient to evaluate policy without a custom kernel build.
- **Observed:** Hermes process RSS was approximately 745,640 KiB, Hermes Desktop zygotes around 558,084 KiB and 131,468 KiB, Chrome probe around 498,612 KiB, and **three** semantic-memory processes around 313,852, 294,108, and 48,172 KiB. This is direct evidence for deduplication before kernel work.
- **Observed:** rtw89 parameters report ASPM L1/L1SS, clkreq, and power-save mitigations enabled (`Y`), yet the current boot log contains firmware PC dumps, `SER catches error: 0x1001`, and `R_AX_HALT_C2H = 0x1002`. This rejects the hypothesis that the existing module parameters alone solve the device.
- **Source-reported:** Linux PSI exposes CPU, memory, and I/O stall metrics and supports cgroup-v2 pressure files; systemd-oomd uses PSI and cgroup lifecycle; sched_ext is a BPF-extensible scheduler class; Fedora documents swap-on-zram and systemd-oomd defaults; kernel documentation describes amd-pstate, MGLRU, BPF, EFI stub, and TPM event logging.
- **Proposed:** ranked candidates, thresholds, and acceptance tests below. Thresholds are admission criteria, not claims about current performance.
- **Blocked:** any persistent boot argument, module replacement, Secure Boot/UEFI change, service enablement, package installation, or custom kernel build in this read-only phase.

## Current diagnosis and ROI model

Measure each candidate against a baseline with the same Chrome profile, Hermes workload, semantic-memory corpus, Wi-Fi AP, power mode, and kernel. Record p50/p95 UI input-to-paint proxy, Hermes request latency, semantic-memory RSS, major faults, PSI, swap/zram activity, battery discharge rate, Wi-Fi outage count, and recovery time. A candidate is admitted only when it improves the target metric without a regression in the guard metrics.

Priority is `impact × confidence × reversibility ÷ maintenance cost`. Reliability and memory isolation outrank novelty.

## Ranked candidates

### R1 — Single semantic-memory owner and cgroup policy (highest ROI)

**Problem/evidence:** three semantic-memory workers are live, while the architecture invariant requires one heavyweight owner and thin clients. This is a direct, repeatable memory tax and likely creates embedding/index contention.

**Design:** make one supervised semantic-memory owner authoritative; route clients through the existing IPC/MCP path; place Hermes, Chrome personal, Chrome automation, memory owner, and experimental profiles in named systemd scopes/cgroups. Set only bounded CPU/memory/IO policies after measuring normal peaks. Keep expensive profiles opt-in.

**Why not kernel customisation:** cgroup v2 and scheduler/resource controls already provide the needed primitives.

**Acceptance:** over three cold starts and a representative 30-minute session: exactly one owner; no duplicate worker; total memory RSS falls by at least 300 MiB versus baseline; semantic-memory p95 request latency does not worsen >10%; no OOM kill; Hermes UI p95 proxy does not regress >5%.

**Rollback:** stop the policy/owner change and restore the prior launcher/service topology; boot and retain the stock kernel. No data deletion.

### R2 — PSI + systemd-oomd as an evidence-backed guardrail

**Problem/evidence:** memory pressure exists, but systemd-oomd is inactive. A 14 GiB system running Chrome, Hermes, and local embeddings needs graceful profile shedding rather than an uncontrolled kernel OOM.

**Design:** collect system and per-cgroup PSI; configure oomd only for disposable experimental/automation scopes, never the memory owner or personal session by default. Use `ManagedOOMMemoryPressure=kill` only after observing pressure windows and testing victim ordering.

**Acceptance:** synthetic stress in a disposable scope triggers the intended scope termination before global OOM; personal Chrome, Hermes, and memory owner survive; `oomctl dump` and journal evidence identify the victim; recovery starts within 30 seconds; no false kill in a 2-hour normal workload. Define baseline pressure window and threshold from captured data rather than copying a universal number.

**Rollback:** disable/remove the drop-in and stop the policy service; verify `systemd-oomd` inactive and normal cgroups restored. Stock kernel remains bootable.

### R3 — zram and MGLRU measurement/tuning

**Problem/evidence:** zram is already active and compressing effectively (498.7 MiB from 693.6 MiB); MGLRU is compiled/enabled. This is promising, but current data does not prove benefit or correct sizing.

**Design:** retain zstd and MGLRU. Benchmark current settings against a bounded alternative (size/priority only) under Chrome + semantic-memory + controlled memory pressure. Do not add a reclaim patch. Enable MGLRU statistics only in a test profile if available; avoid permanent debug overhead.

**Acceptance:** under a repeatable pressure workload, p95 Hermes latency and UI proxy stay within 5% of baseline, swap-in storm is reduced or unchanged, zram compression ratio remains beneficial, and no device lockup occurs across 3 runs. Battery and idle power must not regress >5% in a 30-minute idle sample.

**Rollback:** restore prior zram-generator settings and boot defaults; stop the test profile. No kernel change is required.

### R4 — eBPF observability; narrowly scoped egress control later

**Problem/evidence:** isolated profiles and Tailscale require auditability, but kernel-level filtering can silently break Chrome, Hermes, DNS, or Tailscale.

**Design:** first deploy read-only tracing (process/cgroup lifecycle, network connects, scheduler/pressure events) with bounded ring buffers and no payload capture. Only consider cgroup-BPF egress deny rules for an explicit Privacy/Experimental profile after an allowlist is derived from observed flows. Keep firewalld as the default inbound boundary.

**Acceptance:** observation mode loses <1% events under a stress run, adds <2% CPU, and produces auditable per-cgroup records without secrets. For enforcement, test DNS, HTTPS, Tailscale, Chrome updates, Hermes providers, and local memory IPC; deny-by-default must fail closed and be reversible.

**Rollback:** detach the BPF programs and remove the profile hook; verify connectivity and firewalld state. Never make enforcement the only recovery path.

### R5 — Wi-Fi driver/firmware/kernel A-B evaluation (reliability, not novelty)

**Problem/evidence:** RTL8852BE-VT/rtw89 has a live firmware crash (`SER`, firmware PC, `R_AX_HALT_C2H=0x1002`) despite current module mitigations. This is the strongest hardware-specific risk.

**Design:** preserve the stock kernel. Capture firmware package/version, PCIe `LnkCtl` on bridge and endpoint, disconnect counts, and link recovery time. A/B a newer supported Fedora kernel/firmware in a disposable boot or external qualification environment; evaluate the upstream rtw89 changes/backport only if the regression is reproducible and the patch is narrowly reviewable. Prefer replacing the adapter if reliability remains unacceptable.

**Acceptance:** 24-hour normal use plus repeated throughput/suspend cycles: zero new SER/firmware crash events, zero unexplained disconnects, and recovery <10 seconds when AP is intentionally cycled. Compare battery/idle power. A driver change is admitted only with a reproducible before/after receipt.

**Rollback:** select the retained stock kernel and prior firmware; remove the experimental kernel/module from the test medium only after confirming the stock boot. Do not use `pcie_aspm=off` persistently in this phase; it is a candidate mitigation with a system-wide power trade-off and requires explicit approval.

### R6 — UKI + measured boot + Secure Boot (security/reproducibility gate)

**Problem/evidence:** TPM2 exists, but Secure Boot is disabled and `bootctl` reports GRUB and no measured UKI. This matters for the encrypted workstation's trust story, not runtime throughput.

**Design:** build and verify a Fedora 44 UKI in VM/external media first; document signing ownership, PCR policy, recovery path, and signed rollback kernel. Admit only after backup/restore, VM, and external qualification gates. Never enroll keys or alter UEFI in this task.

**Acceptance:** VM and external-media boots succeed with Secure Boot on in the qualification environment; PCR/event-log measurements are recorded; LUKS unlock and recovery path work; stock fallback remains bootable; update and rollback both pass. No secrets or recovery keys enter this repository.

**Rollback:** select the signed stock/fallback entry; restore the previous boot entry using the approved recovery medium. UEFI changes require a separate explicit approval gate.

### R7 — sched_ext policy experiment (optional, low prior)

**Problem/evidence:** sched_ext is available, but disabled; no evidence shows scheduler starvation or latency as the bottleneck. `scx_loader` being active is not evidence that a scheduler is active.

**Design:** test an existing, auditable scheduler in an isolated boot/profile only. Do not write a custom scheduler. Compare stock PREEMPT_DYNAMIC against sched_ext with Hermes, Chrome, embedding, compile, and idle workloads.

**Acceptance:** 10-run comparison: Hermes/UI p95 proxy improves >=10% or tail latency variance drops >=15%, while throughput is not worse >3%, battery discharge is not worse >5%, suspend/resume has zero failures, and `nr_rejected`/scheduler errors remain zero. If not, reject.

**Rollback:** disable sched_ext/loader selection and reboot into the retained stock entry. A scheduler must never be required for recovery.

## Explicitly rejected custom kernel work

- **Custom scheduler:** rejected absent the R7 benchmark delta; policy is already available through sched_ext.
- **Custom reclaim/MGLRU patch:** rejected because MGLRU and zram are present and R3 can measure configuration effects first.
- **Custom AMD power-management patch:** rejected; use the documented amd-pstate driver and measure `performance`, `schedutil`, or platform defaults before considering upstream bug work.
- **Kernel egress firewall:** rejected as default; cgroup-BPF/firewalld provide safer, reversible layers.
- **Wi-Fi patch immediately:** rejected until firmware/kernel A-B evidence identifies a specific missing upstream fix. The observed crash justifies investigation, not speculative patching.

## Audit-rerunnable read-only evidence commands

```bash
cd /home/sikmindz/Projects/hermes-workbench-os
cat AGENTS.md
uname -a; cat /etc/os-release; hostnamectl
free -h; cat /proc/cmdline
lscpu; lspci -nnk
cat /proc/pressure/{cpu,memory,io}
zramctl
systemctl is-active systemd-oomd
systemctl status scx_loader --no-pager
for f in /sys/kernel/sched_ext/*; do printf '%s=' "$f"; cat "$f"; done
 grep -E 'CONFIG_(SCHED_CLASS_EXT|PSI|LRU_GEN|ZRAM|BPF|CGROUP)' /boot/config-$(uname -r)
ps -eo pid,ppid,comm,rss,%mem,cmd --sort=-rss | grep -Ei 'hermes|semantic|memory'
for f in /sys/module/rtw89_pci/parameters/* /sys/module/rtw89_core/parameters/*; do [ -f "$f" ] && printf '%s=' "$f" && cat "$f"; done
journalctl -k -b --no-pager | grep -Ei 'rtw89|SER|fw PC'
mokutil --sb-state
bootctl status
```

## Sources

- Linux sched_ext: https://docs.kernel.org/scheduler/sched-ext.html
- Linux PSI: https://docs.kernel.org/accounting/psi.html
- Linux MGLRU: https://docs.kernel.org/admin-guide/mm/multigen_lru.html
- Linux amd-pstate: https://docs.kernel.org/admin-guide/pm/amd-pstate.html
- Linux eBPF documentation: https://docs.kernel.org/bpf/
- Fedora swap-on-zram: https://fedoraproject.org/wiki/Changes/SwapOnZRAM
- Fedora systemd-oomd: https://fedoraproject.org/wiki/Changes/EnableSystemdOomd
- systemd resource control / oomd: https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html
- Linux EFI stub: https://docs.kernel.org/admin-guide/efi-stub.html
- Linux TPM event log: https://docs.kernel.org/security/tpm/tpm_event_log.html
- Linux Wireless ASPM notes: https://wireless.docs.kernel.org/en/latest/en/users/documentation/aspm.html
- Linux amd-pstate and amdgpu primary documentation as above.

## Completion receipt

**Changed file:** `/home/sikmindz/Projects/hermes-workbench-os/docs/KERNEL-AND-RUNTIME-ROI.md` only.

**Commands/evidence used:** the commands in the audit block, plus live `git status`/repository discovery, targeted kernel/Fedora web searches, and primary-document URL lookup above.

**Issues:** the supplied path is not currently a Git worktree (`git status` returned “not a git repository”); the live host is Nobara 43 although the target contract is Fedora 44. Therefore no build, VM, external-media, or deployment state is claimed. No package, service, kernel, UEFI, or disk was modified.
