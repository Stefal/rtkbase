#!/bin/bash

# ------------------------------------------------------------
# CONFIG LOADING
# ------------------------------------------------------------

CONFIG_FILE="/etc/net-state.conf"
[ -f "$CONFIG_FILE" ] && source "$CONFIG_FILE"

# Defaults
IFACE="${IFACE:-$(ip -o link show | awk -F': ' '$2 !~ /lo/ {print $2; exit}')}"
LOG_FILE="${LOG_FILE:-/var/log/net-state.log}"
DEBUG="${DEBUG:-0}"
STABLE_THRESHOLD="${STABLE_THRESHOLD:-3}"
ENABLE_SHARED_IF_NO_DHCP="${ENABLE_SHARED_IF_NO_DHCP:-0}"

STATE_FILE="/run/net-state.state"

STABLE_STATE=""
STABLE_COUNT=0

# ------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------

log() {
    local LEVEL="$1"
    shift
    local MSG="$*"
    local LINE="$(date '+%F %T') [$LEVEL] $MSG"

    echo "$LINE" >> "$LOG_FILE"
    logger -t net-state "$LINE"
}

debug() {
    [ "$DEBUG" -eq 1 ] && log "DEBUG" "$*"
}

status() {

    CURRENT=$(get_state)

    IP=$(ip -4 addr show dev "$IFACE" | awk '/inet / {print $2}')
    IP=${IP:-none}

    has_dhcp
    DHCP=$?

    has_activity
    ACT=$?

    has_neighbors
    NEI=$?

    echo "----------------------------------------"
    echo "Interface : $IFACE"
    echo "State     : ${CURRENT:-unknown}"
    echo "IP        : $IP"
    echo ""
    echo "Detection :"
    echo "  DHCP     : $([ "$DHCP" -eq 0 ] && echo yes || echo no)"
    echo "  Activity : $([ "$ACT" -eq 0 ] && echo yes || echo no)"
    echo "  Neighbors: $([ "$NEI" -eq 0 ] && echo yes || echo no)"
    echo ""

    # Predicted decision (without applying)
    if [ "$DHCP" -eq 0 ]; then
        DECISION="CLIENT (DHCP detected)"
    elif [ "$CURRENT" = "SHARED" ]; then
        DECISION="SHARED (sticky mode)"
    elif [ "$ACT" -ne 0 ] && [ "$NEI" -ne 0 ]; then
        if [ "$ENABLE_SHARED_IF_NO_DHCP" -eq 1 ]; then
            DECISION="SHARED (isolated + config)"
        else
            DECISION="DIRECT (isolated)"
        fi
    else
        DECISION="IDLE (network detected, without DHCP)"
    fi

    echo "Decision  : $DECISION"
    echo "----------------------------------------"
}

# ------------------------------------------------------------
# STATE
# ------------------------------------------------------------

get_state() {
    cat "$STATE_FILE" 2>/dev/null
}

set_state() {
    echo "$1" > "$STATE_FILE"
}

# ------------------------------------------------------------
# DETECTION
# ------------------------------------------------------------

has_dhcp() {
    local OUT
    OUT=$(timeout 5 tcpdump -i "$IFACE" -n -c 2 'udp port 67 or 68' 2>/dev/null)

    if echo "$OUT" | grep -q BOOTP; then
        debug "DHCP: detected"
        return 0
    else
        debug "DHCP: not detected"
        return 1
    fi
}

has_activity() {
    if timeout 3 tcpdump -i "$IFACE" -c 5 >/dev/null 2>&1; then
        debug "ACTIVITY: yes"
        return 0
    else
        debug "ACTIVITY: no"
        return 1
    fi
}

has_neighbors() {
    local N
    N=$(ip neigh show dev "$IFACE" | grep -vc FAILED)

    debug "NEIGHBORS: count=$N"

    [ "$N" -gt 1 ]
}

debug_snapshot() {
    local IP
    IP=$(ip -4 addr show dev "$IFACE" | awk '/inet / {print $2}')

    debug "SNAPSHOT iface=$IFACE ip=${IP:-none}"
}

# ------------------------------------------------------------
# ACTIONS
# ------------------------------------------------------------

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

# ------------------------------------------------------------
# ANTI-FLAPPING
# ------------------------------------------------------------

apply_state_if_stable() {
    local NEW="$1"

    if [ "$NEW" = "$STABLE_STATE" ]; then
        STABLE_COUNT=$((STABLE_COUNT + 1))
    else
        STABLE_STATE="$NEW"
        STABLE_COUNT=1
    fi

    debug "eval=$NEW stable=$STABLE_STATE count=$STABLE_COUNT current=$(get_state)"

    [ "$STABLE_COUNT" -lt "$STABLE_THRESHOLD" ] && return

    CURRENT=$(get_state)

    [ "$CURRENT" = "$STABLE_STATE" ] && return

    case "$STABLE_STATE" in
        CLIENT) apply_client ;;
        DIRECT) apply_direct ;;
        IDLE)   apply_idle ;;
        SHARED) apply_shared ;;
    esac

    log "INFO" "STATE CHANGE: $CURRENT → $STABLE_STATE"
    set_state "$STABLE_STATE"
}

# ------------------------------------------------------------
# CORE LOGIC
# ------------------------------------------------------------

evaluate() {

    CURRENT=$(get_state)

    debug "=============================="
    debug "EVALUATION START state=$CURRENT"

    debug_snapshot

    has_dhcp
    DHCP=$?

    has_activity
    ACT=$?

    has_neighbors
    NEI=$?

    debug "RESULTS: dhcp=$DHCP activity=$ACT neighbors=$NEI"

    # 1. DHCP → CLIENT
    if [ "$DHCP" -eq 0 ]; then
        debug "DECISION: CLIENT (DHCP server detected)"
        apply_state_if_stable "CLIENT"
        return
    fi

    # 2. Stay SHARED unless DHCP appears
    if [ "$CURRENT" = "SHARED" ]; then
        debug "DECISION: stay SHARED (no DHCP)"
        return
    fi

    # 3. Isolated link
    if [ "$ACT" -ne 0 ] && [ "$NEI" -ne 0 ]; then
        if [ "$ENABLE_SHARED_IF_NO_DHCP" -eq 1 ]; then
            debug "DECISION: SHARED (isolated + config enabled)"
            apply_state_if_stable "SHARED"
        else
            debug "DECISION: DIRECT (isolated)"
            apply_state_if_stable "DIRECT"
        fi
        return
    fi

    # 4. Network present but no DHCP
    debug "DECISION: IDLE (activity but no DHCP)"
    apply_state_if_stable "IDLE"
}

# ------------------------------------------------------------
# ENTRYPOINT
# ------------------------------------------------------------

case "$1" in
    --event|--check)
        evaluate
        ;;
    --status)
        status
        ;;
    *)
        echo "Usage: $0 --event | --check | --status"
        exit 1
        ;;
esac