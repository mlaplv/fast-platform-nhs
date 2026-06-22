#!/bin/bash
# Script to clean up orphaned/zombie 'docker logs' client processes on VPS

echo "🧹 [SOC Maintenance] Scanning for orphaned docker logs processes..."

# Find pids of docker logs commands running under current user
# Exclude the current grep process and the script itself
PIDS=$(ps -eo pid,etime,args | grep -E "docker logs|docker compose logs" | grep -v grep | grep -v "clean_zombie_logs.sh" | awk '{print $1}')

if [ -z "$PIDS" ]; then
    echo "✅ No orphaned docker logs processes found."
    exit 0
fi

echo "Found the following docker logs processes:"
ps -eo pid,etime,args | grep -E "docker logs|docker compose logs" | grep -v grep | grep -v "clean_zombie_logs.sh"

# Let's kill them
for pid in $PIDS; do
    echo "Killing process $pid..."
    kill -9 $pid 2>/dev/null
done

echo "✅ Orphaned docker logs processes cleaned."
