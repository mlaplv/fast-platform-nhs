#!/bin/bash
# Script to clean up orphaned/zombie 'docker logs' client processes on VPS

echo "🧹 [SOC Maintenance] Scanning for orphaned docker logs processes..."

# Find PIDs of docker logs / docker compose logs processes that are orphaned (PPID = 1 and TTY = ?)
PIDS=$(ps -eo pid,ppid,tty,args | grep -E "docker logs|docker compose logs" | grep -v grep | awk '$2 == 1 && $3 == "?" {print $1}')

if [ -z "$PIDS" ]; then
    echo "✅ No orphaned docker logs processes found."
    exit 0
fi

echo "Found the following orphaned docker logs processes:"
ps -eo pid,ppid,tty,args | grep -E "docker logs|docker compose logs" | grep -v grep | awk '$2 == 1 && $3 == "?"'

# Let's kill them
for pid in $PIDS; do
    echo "Killing process $pid..."
    kill -9 $pid 2>/dev/null
done

echo "✅ Orphaned docker logs processes cleaned."
