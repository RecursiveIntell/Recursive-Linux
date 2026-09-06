#!/usr/bin/env bash
# Low-overhead atomic workstation health projection.
set -euo pipefail
interval="${HWOS_HEALTH_INTERVAL:-60}"
once=0
if [[ ${1:-} == --once ]]; then once=1
elif [[ $# != 0 ]]; then printf 'Usage: %s [--once]\n' "$0" >&2; exit 2
fi
[[ "$interval" =~ ^[0-9]+$ ]] && ((interval > 0)) || { echo 'invalid interval' >&2; exit 2; }
state_dir="${XDG_STATE_HOME:-$HOME/.local/state}/hermes-workbench"
state_file="$state_dir/system-health.json"
mkdir -p "$state_dir"
while true; do
    tmp="$state_file.tmp.$$"
    read -r mem_total mem_available < <(awk '/MemTotal:/{t=$2} /MemAvailable:/{a=$2} END{print t,a}' /proc/meminfo)
    read -r swap_total swap_free < <(awk '/SwapTotal:/{t=$2} /SwapFree:/{f=$2} END{print t,f}' /proc/meminfo)
    read -r disk_total disk_available < <(df -Pk / | awk 'NR==2 {print $2,$4}')
    failed_system=$(systemctl --failed --no-legend 2>/dev/null | wc -l)
    failed_user=$(systemctl --user --failed --no-legend 2>/dev/null | wc -l)
    wifi_state=$(nmcli -t -f TYPE,STATE device 2>/dev/null | awk -F: '$1=="wifi"{print $2; exit}')
    printf '{\n  "captured_at": "%s",\n  "memory_total_kib": %s,\n  "memory_available_kib": %s,\n  "swap_total_kib": %s,\n  "swap_used_kib": %s,\n  "root_total_kib": %s,\n  "root_available_kib": %s,\n  "failed_system_units": %s,\n  "failed_user_units": %s,\n  "wifi_state": "%s"\n}\n' \
        "$(date -Iseconds)" "$mem_total" "$mem_available" "$swap_total" "$((swap_total-swap_free))" \
        "$disk_total" "$disk_available" "$failed_system" "$failed_user" "${wifi_state:-unknown}" > "$tmp"
    mv "$tmp" "$state_file"
    ((once == 1)) && exit 0
    sleep "$interval"
done
