#!/usr/bin/env bash
# Report-only disk governor. It never deletes or offloads data.
set -euo pipefail
notify=1
if [[ ${1:-} == --no-notify && $# == 1 ]]; then notify=0
elif [[ $# != 0 ]]; then printf 'Usage: %s [--no-notify]\n' "$0" >&2; exit 2
fi
report=$(/usr/bin/df -Pk /)
read -r filesystem total used available capacity mounted <<< "${report##*$'\n'}"
if [[ ! $total =~ ^[0-9]+$ || ! $available =~ ^[0-9]+$ || $total == 0 ]]; then
    printf 'REPORT_ONLY disk measurement failed\n' >&2
    exit 1
fi
free_pct=$((available * 100 / total))
printf 'REPORT_ONLY root_free_pct=%s available_kib=%s cleanup_enabled=false offload_enabled=false\n' "$free_pct" "$available"
if ((notify && free_pct < 25)) && command -v notify-send >/dev/null 2>&1; then
    urgency=normal; if ((free_pct < 15)); then urgency=critical; fi
    notify-send -u "$urgency" -a 'Disk Governor' 'Disk space: review required' \
        "Root has ${free_pct}% available. Nothing was deleted or moved." || true
fi
