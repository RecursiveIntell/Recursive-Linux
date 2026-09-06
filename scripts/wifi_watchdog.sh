#!/usr/bin/env bash
# wifi-watchdog v5 — portable RTL8852BE stall detection and safe recovery.
# Never unloads the rtw89 driver: that path caused a verified kernel oops on
# this laptop. Recovery is bounded to a NetworkManager Wi-Fi radio cycle.
set -euo pipefail

PREFERRED_INTERFACE="${HWOS_WIFI_INTERFACE:-}"
PREFERRED_CONNECTION="${HWOS_WIFI_CONNECTION:-}"
HEALTHY_INTERVAL="${HWOS_WIFI_HEALTHY_INTERVAL:-10}"
DEGRADED_INTERVAL="${HWOS_WIFI_DEGRADED_INTERVAL:-2}"
STALL_THRESHOLD="${HWOS_WIFI_STALL_THRESHOLD:-2}"
PING_TIMEOUT="${HWOS_WIFI_PING_TIMEOUT:-2}"
RECOVERY_COOLDOWN="${HWOS_WIFI_RECOVERY_COOLDOWN:-120}"
MAX_RECOVERIES_PER_HOUR="${HWOS_WIFI_MAX_RECOVERIES_PER_HOUR:-3}"
STATE_DIR="${HWOS_WIFI_STATE_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/hermes-workbench}"
STATE_FILE="$STATE_DIR/wifi-watchdog-state.json"
COUNT_FILE="$STATE_DIR/wifi-watchdog-recovery-count"
TRIGGER_FILE="$STATE_DIR/wifi-watchdog-crash"
LOCK_FILE="$STATE_DIR/wifi-watchdog.lock"

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    printf '%s\n' "$msg" >&2
    if [[ -z "${JOURNAL_STREAM:-}" ]]; then
        printf '%s\n' "$msg" >> "$STATE_DIR/wifi-watchdog.log"
    fi
}

kernel_line_is_crash() {
    local line="${1:-}"
    case "$line" in
        *"SER catches error:"*|*"R_AX_HALT_C2H ="*|*"FW BADADDR ="*|*"[ERR]fw PC ="*) return 0 ;;
        *) return 1 ;;
    esac
}

default_gateway() {
    local iface="${1:-}"
    if [[ -n "$iface" ]]; then
        ip -4 route show default dev "$iface" 2>/dev/null | awk 'NR==1 {print $3}'
    else
        ip -4 route show default 2>/dev/null | awk 'NR==1 {print $3}'
    fi
}

resolve_interface() {
    if [[ -n "$PREFERRED_INTERFACE" ]] && ip -o link show "$PREFERRED_INTERFACE" >/dev/null 2>&1; then
        printf '%s\n' "$PREFERRED_INTERFACE"
        return 0
    fi
    nmcli -t -f DEVICE,TYPE device status 2>/dev/null |
        awk -F: '$2=="wifi" && $1 !~ /^p2p-dev-/ {print $1; exit}'
}

active_connection() {
    local iface="${1:-}"
    if [[ -n "$PREFERRED_CONNECTION" ]]; then
        printf '%s\n' "$PREFERRED_CONNECTION"
        return 0
    fi
    [[ -n "$iface" ]] || return 1
    nmcli -g GENERAL.CONNECTION device show "$iface" 2>/dev/null | awk 'NF && $0!="--" {print; exit}'
}

ping_ok() {
    local iface="${1:-}" gateway
    [[ -n "$iface" ]] || return 1
    gateway=$(default_gateway "$iface")
    [[ -n "$gateway" ]] || return 1
    ping -c 1 -W "$PING_TIMEOUT" -I "$iface" "$gateway" >/dev/null 2>&1
}

write_state() {
    local status="$1" last_recovery="$2" method="$3" failures="$4" total="$5" daily="$6" uptime="$7"
    local tmp="$STATE_FILE.tmp.$$"
    printf '{\n  "status": "%s",\n  "last_check": "%s",\n  "last_recovery_epoch": %s,\n  "last_recovery_method": "%s",\n  "consecutive_failures": %s,\n  "total_recoveries": %s,\n  "recoveries_today": %s,\n  "uptime_seconds": %s\n}\n' \
        "$status" "$(date -Iseconds)" "$last_recovery" "$method" "$failures" "$total" "$daily" "$uptime" > "$tmp"
    mv "$tmp" "$STATE_FILE"
}

increment_count() {
    local today total=0 daily=0 prior_date=""
    today=$(date +%F)
    if [[ -r "$COUNT_FILE" ]]; then
        read -r total daily prior_date < "$COUNT_FILE" || true
    fi
    total=$((total + 1))
    if [[ "$prior_date" == "$today" ]]; then daily=$((daily + 1)); else daily=1; fi
    printf '%s %s %s\n' "$total" "$daily" "$today" > "$COUNT_FILE"
    printf '%s %s\n' "$total" "$daily"
}

wait_for_interface() {
    local seconds="$1" iface
    while ((seconds-- > 0)); do
        iface=$(resolve_interface || true)
        if [[ -n "$iface" ]]; then printf '%s\n' "$iface"; return 0; fi
        sleep 1
    done
    return 1
}

wait_for_connectivity() {
    local iface="$1" seconds="${2:-20}"
    while ((seconds-- > 0)); do
        if ping_ok "$iface"; then return 0; fi
        sleep 1
    done
    return 1
}

recover_wifi() {
    local iface connection
    iface=$(resolve_interface || true)
    connection=$(active_connection "$iface" || true)
    log "Recovery: cycling NetworkManager Wi-Fi radio; kernel module remains loaded"
    nmcli radio wifi off >/dev/null 2>&1 || return 1
    sleep 3
    nmcli radio wifi on >/dev/null 2>&1 || return 1
    iface=$(wait_for_interface 15 || true)
    [[ -n "$iface" ]] || return 1
    if ! timeout 20 nmcli device connect "$iface" >/dev/null 2>&1; then
        if [[ -n "$connection" ]]; then
            timeout 20 nmcli connection up "$connection" iface "$iface" >/dev/null 2>&1 ||
                timeout 20 nmcli connection up "$connection" >/dev/null 2>&1 || return 1
        else
            return 1
        fi
    fi
    wait_for_connectivity "$iface" 20
}

watch_kernel() {
    if ! journalctl -k -b -n 1 --no-pager >/dev/null 2>&1; then
        log "Kernel journal unavailable; continuing with connectivity probes"
        return 0
    fi
    journalctl -k -f --no-pager --since now -o short-iso 2>/dev/null |
    while IFS= read -r line; do
        if kernel_line_is_crash "$line"; then
            printf '%s\n' "$(date +%s)" > "$TRIGGER_FILE"
            log "Kernel reported an rtw89 firmware fault"
        fi
    done
}

if [[ "${WIFI_WATCHDOG_LIB_ONLY:-0}" == "1" ]]; then
    return 0 2>/dev/null || exit 0
fi

for command in ip ping nmcli journalctl awk flock timeout; do
    command -v "$command" >/dev/null 2>&1 || { printf 'missing command: %s\n' "$command" >&2; exit 1; }
done
for value in "$HEALTHY_INTERVAL" "$DEGRADED_INTERVAL" "$STALL_THRESHOLD" "$PING_TIMEOUT" "$RECOVERY_COOLDOWN" "$MAX_RECOVERIES_PER_HOUR"; do
    [[ "$value" =~ ^[0-9]+$ ]] || { printf 'watchdog timing values must be integers\n' >&2; exit 2; }
done

mkdir -p "$STATE_DIR"
exec 9>"$LOCK_FILE"
flock -n 9 || { log "Another watchdog instance owns $LOCK_FILE"; exit 0; }
: > "$TRIGGER_FILE"
watch_kernel &
watcher_pid=$!
trap 'kill "$watcher_pid" 2>/dev/null || true; rm -f "$TRIGGER_FILE"' EXIT

start_time=$(date +%s)
last_recovery=0
last_method="none"
consecutive_failures=0
recoveries_this_hour=0
hour_started=$start_time
total=0
daily=0
if [[ -r "$COUNT_FILE" ]]; then read -r total daily _ < "$COUNT_FILE" || true; fi
log "wifi-watchdog v5 started; recovery uses NetworkManager radio only"

while true; do
    now=$(date +%s)
    if ((now - hour_started >= 3600)); then recoveries_this_hour=0; hour_started=$now; fi
    iface=$(resolve_interface || true)
    fault=0
    if [[ -s "$TRIGGER_FILE" ]]; then
        trigger=$(<"$TRIGGER_FILE")
        : > "$TRIGGER_FILE"
        if [[ "$trigger" =~ ^[0-9]+$ ]] && ((now - trigger < 15)); then fault=1; fi
    fi
    if [[ -n "$iface" ]] && ping_ok "$iface"; then
        consecutive_failures=0
        status="healthy"
        interval=$HEALTHY_INTERVAL
    else
        consecutive_failures=$((consecutive_failures + 1))
        status=$([[ -n "$iface" ]] && printf 'degraded' || printf 'missing_interface')
        interval=$DEGRADED_INTERVAL
    fi
    if ((fault == 1 || consecutive_failures >= STALL_THRESHOLD)); then
        if ((now - last_recovery >= RECOVERY_COOLDOWN && recoveries_this_hour < MAX_RECOVERIES_PER_HOUR)); then
            if recover_wifi; then
                read -r total daily < <(increment_count)
                last_recovery=$now
                last_method="nm_radio_cycle"
                recoveries_this_hour=$((recoveries_this_hour + 1))
                status="healthy"
                log "Recovery #$total succeeded"
            else
                status="recovery_failed"
                log "Recovery failed; leaving driver loaded"
            fi
        else
            log "Recovery deferred by cooldown/rate limit"
        fi
        consecutive_failures=0
        interval=$HEALTHY_INTERVAL
    fi
    write_state "$status" "$last_recovery" "$last_method" "$consecutive_failures" "$total" "$daily" "$((now - start_time))"
    sleep "$interval"
done
