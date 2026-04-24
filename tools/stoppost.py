#!/usr/bin/env python3

"""
This script inspects systemd journal logs for the pyruse.service unit
to determine why it stopped a service that subsequently executed this script.

It uses the systemd journal API directly (no journalctl subprocess)
to retrieve logs associated with the current INVOCATION_ID.

Rationale:
    The str2str tool from RTKLib does not reliably stop itself when errors occur
    (e.g., invalid NTRIP caster credentials, GNSS receiver disconnection).
    This script helps surface the actual failure reason by relying on
    pyruse.service which monitors str2str services and enforces stopping logic.

Typical usage context:
    - Executed as part of a systemd service lifecycle (e.g., ExecStopPost)
    - Helps propagate or expose the failure reason from pyruse.service

Exit codes:
    0: No relevant log entry found.
    1: Matching log entry found (treated as error).
    2: Missing INVOCATION_ID environment variable.
"""

import os
import sys
import time
from typing import Optional
from enum import Enum, unique
from systemd import journal

SERVICE_NAME = "pyruse.service"
TIMEOUT = 5.0
RETRY_INTERVAL = 0.3
MAX_LINES = 200

@unique
class Level(Enum):
    EMERG = 0
    ALERT = 1
    CRIT = 2
    ERR = 3
    WARNING = 4
    NOTICE = 5
    INFO = 6
    DEBUG = 7


def log(level: Level, message: str, invocation_id: Optional[str] = None) -> None:
    journal.send(
        message,
        PRIORITY=level.value,
        SYSLOG_IDENTIFIER=get_unit_name(),
        INVOCATION_ID=invocation_id or os.environ.get("INVOCATION_ID", ""),
    )

def get_unit_name() -> str:
    """
    Get unit name which launch this script

    Return:
        The unit name, or None.
    """

    if len(sys.argv) > 1:
        return os.path.splitext(sys.argv[1])[0]
    return "poststop.py"

def query_journal(invocation_id: str) -> Optional[str]:
    """
    Query systemd journal directly for pyruse.service entries matching INVOCATION_ID.

    Args:
        invocation_id: systemd INVOCATION_ID to filter logs.

    Returns:
        The most recent matching log message, or None.
    """
    try:
        reader = journal.Reader()
        # Only logs from this service
        reader.add_match(_SYSTEMD_UNIT=SERVICE_NAME)
        # Start from the end
        reader.seek_tail()

        match_line = None

        lines_checked = 0
        while lines_checked < MAX_LINES:
            entry = reader.get_previous()
            if not entry:
                break

            lines_checked += 1
            message = entry.get("MESSAGE", "")

            if invocation_id in message:
                match_line = message
                break

        return match_line

    except Exception as e:
        log(Level.ERR, f"Failed to read systemd journal: {e}", "ERROR")
        return None


def extract_error_message(message: str, invocation_id: str) -> str:
    """
    Extract error message from journal message if formatted with INVOCATION_ID.
    """
    marker = f"{invocation_id}: "
    if marker in message:
        return message.split(marker, 1)[1]
    return message


def main() -> None:
    """
    Look up the current INVOCATION_ID in systemd journal logs and report
    a matching error if found.
    """
    invocation_id = os.environ.get("INVOCATION_ID")

    if not invocation_id:
        log(Level.ERR, "Missing INVOCATION_ID environment variable", "ERROR")
        sys.exit(2)

    start_time = time.time()
    match_line = None

    while time.time() - start_time < TIMEOUT:
        match_line = query_journal(invocation_id)

        if match_line:
            break

        time.sleep(RETRY_INTERVAL)

    if match_line:
        error_msg = extract_error_message(match_line, invocation_id)
        log(Level.ERR, error_msg, "ERROR")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()