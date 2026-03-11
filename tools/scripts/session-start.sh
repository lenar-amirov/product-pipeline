#!/bin/bash
# session-start.sh — launched by ttyd as the shell command for each PM user.
# If a state file exists (written by Flask /open/<name>), cd into that initiative
# and launch claude. Falls back to a plain login shell in either case.

STATE="/tmp/pm-session-$(whoami)"

if [ -f "$STATE" ]; then
    TARGET=$(cat "$STATE")
    rm -f "$STATE"
    cd "$TARGET" 2>/dev/null
fi

exec bash -l
