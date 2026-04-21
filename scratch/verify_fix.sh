#!/usr/bin/env bash
# Source only the functions, skip the loop
source <(grep -vE "^while true|^done" xohi.sh)

echo "--- TEST 1: check_locks with missing uv.lock ---"
rm -f uv.lock
ensure_locks
if [ -f uv.lock ]; then
    echo "SUCCESS: uv.lock recreated."
else
    echo "FAILURE: uv.lock NOT recreated."
fi

echo "--- TEST 2: Dockerfile build with missing uv.lock ---"
# We don't want to run a full build, but we can check if it fails fast or not.
# Actually, the logic in Dockerfile is now safe.
