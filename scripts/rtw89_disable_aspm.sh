#!/usr/bin/env bash
# Disable PCIe ASPM L0s/L1 on the active RTL8852BE-VT endpoint and its parent.
# The topology is discovered from sysfs; no machine-specific BDF is embedded.
set -euo pipefail

DRIVER_DIR="${RTW89_DRIVER_DIR:-/sys/bus/pci/drivers/rtw89_8852bte}"
SETPCI="${SETPCI:-setpci}"
DRY_RUN="${ASPM_DRY_RUN:-0}"

log() { printf 'rtw89-aspm: %s\n' "$*"; }

setpci_bdf() {
    local raw="$1"
    if [[ "$raw" =~ ^[[:xdigit:]]{4}:([[:xdigit:]]{2}:[[:xdigit:]]{2}\.[[:xdigit:]])$ ]]; then
        printf '%s\n' "${BASH_REMATCH[1]}"
    else
        printf '%s\n' "$raw"
    fi
}

disable_link_aspm() {
    local bdf before after verify
    bdf=$(setpci_bdf "$1")
    before=$($SETPCI -s "$bdf" CAP_EXP+10.w)
    [[ "$before" =~ ^[0-9A-Fa-f]{4}$ ]] || { log "$bdf returned invalid LnkCtl value: $before"; return 1; }
    printf -v after '%04x' "$((16#$before & 0xfffc))"
    if [[ "$DRY_RUN" == "1" ]]; then
        log "$bdf $before -> $after (dry run)"
        return 0
    fi
    $SETPCI -s "$bdf" "CAP_EXP+10.w=$after"
    verify=$($SETPCI -s "$bdf" CAP_EXP+10.w)
    if ((16#$verify & 0x3)); then
        log "$bdf verification failed: $verify"
        return 1
    fi
    log "$bdf $before -> $verify"
}

if [[ "${RTW89_ASPM_LIB_ONLY:-0}" == "1" ]]; then
    return 0 2>/dev/null || exit 0
fi

if [[ ! -d "$DRIVER_DIR" ]]; then
    log "driver directory absent; no matching hardware"
    exit 0
fi

shopt -s nullglob
devices=("$DRIVER_DIR"/*:*)
if ((${#devices[@]} == 0)); then
    log "no bound rtw89_8852bte endpoint; no action"
    exit 0
fi

seen=""
for link in "${devices[@]}"; do
    endpoint=$(basename "$link")
    endpoint_path=$(readlink -f "/sys/bus/pci/devices/$endpoint")
    parent=$(basename "$(dirname "$endpoint_path")")
    for bdf in "$parent" "$endpoint"; do
        case " $seen " in *" $bdf "*) continue ;; esac
        seen="$seen $bdf"
        disable_link_aspm "$bdf"
    done
done
