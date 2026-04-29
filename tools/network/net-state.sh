#!/bin/bash

CONFIG_FILE="/etc/net-state.conf"
[ -f "$CONFIG_FILE" ] && source "$CONFIG_FILE"

IFACE="${IFACE:-$(ip -o link show | awk -F': ' '$2 !~ /lo/ {print $2; exit}')}"
LOG_FILE="${LOG_FILE:-/var/log/net-state.log}"
DEBUG="${DEBUG:-0}"
STABLE_THRESHOLD="${STABLE_THRESHOLD:-3}"
ENABLE_SHARED_IF_NO_DHCP="${ENABLE_SHARED_IF_NO_DHCP:-0}"

STATE_FILE="/run/net-state.state"

STABLE_STATE=""
STABLE_COUNT=0

log() {
    local lvl="$1"
    shift
    local msg="$*"
    echo "$(date '+%F %T') [$lvl] $msg" | tee -a "$LOG_FILE"
    logger -t net-state "$lvl $msg"
}

debug() {
    [ "$DEBUG" -eq 1 ] && log "DEBUG" "$*"
}

get_state() {
    cat "$STATE_FILE" 2>/dev/null
}

set_state() {
    echo "$1" > "$STATE_FILE"
}

has_ip() {
    ip -4 addr show dev "$IFACE" | grep -q "inet "
}

has_activity() {
    timeout 2 tcpdump -i "$IFACE" -c 5 >/dev/null 2>&1
}

has_neighbors() {
    [ "$(ip neigh show dev "$IFACE" | grep -vc FAILED)" -gt 1 ]
}

apply_client() {
    log "INFO" "Applying CLIENT"
    nmcli con up "Wired connection 1"
}

apply_direct() {
    log "INFO" "Applying DIRECT"
    nmcli con up "mode-direct"
}

apply_idle() {
    log "INFO" "Entering IDLE"
}

apply_shared() {
    log "WARN" "Applying SHARED"
    nmcli con up "mode-shared"
}

apply_state_if_stable() {
    local new="$1"

    if [ "$new" = "$STABLE_STATE" ]; then
        STABLE_COUNT=$((STABLE_COUNT + 1))
    else
        STABLE_STATE="$new"
        STABLE_COUNT=1
    fi

    debug "eval=$new stable=$STABLE_STATE count=$STABLE_COUNT current=$(get_state)"

    [ "$STABLE_COUNT" -lt "$STABLE_THRESHOLD" ] && return

    current=$(get_state)

    [ "$current" = "$STABLE_STATE" ] && return

    case "$STABLE_STATE" in
        CLIENT) apply_client ;;
        DIRECT) apply_direct ;;
        IDLE)   apply_idle ;;
        SHARED) apply_shared ;;
    esac

    log "INFO" "STATE CHANGE: $current → $STABLE_STATE"
    set_state "$STABLE_STATE"
}

evaluate() {

    debug "cycle start iface=$IFACE"

    if has_ip; then
        apply_state_if_stable "CLIENT"
        return
    fi

    if ! has_activity && ! has_neighbors; then
        apply_state_if_stable "DIRECT"
        return
    fi

    if has_activity || has_neighbors; then
        apply_state_if_stable "IDLE"
        return
    fi

    if [ "$ENABLE_SHARED_IF_NO_DHCP" -eq 1 ]; then
        apply_state_if_stable "SHARED"
    else
        apply_state_if_stable "IDLE"
    fi
}

case "$1" in
    --event|--check)
        evaluate
        ;;
    *)
        log "ERROR" "usage: --event | --check"
        exit 1
        ;;
esac