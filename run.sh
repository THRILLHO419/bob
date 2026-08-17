#!/usr/bin/env bash
# Pulls the latest version of this tool, then runs it. Just run this instead
# of calling video_shuffler.py directly — you'll always be on the newest code.
set -e
cd "$(dirname "$0")"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git pull --ff-only >/dev/null 2>&1 || echo "warning: could not auto-update (offline?), using local copy" >&2
fi

python3 video_shuffler.py "$@"
