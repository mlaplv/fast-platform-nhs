#!/usr/bin/env bash

# ==============================================================================
# FAST PLATFORM — DEV SYNCHRONIZATION SCRIPT (ELITE V2.2)
# ==============================================================================
# Syncs local codebase modifications to the remote VPS and restarts backend
# services if needed. Uses passwordless Rsync over SSH.

set -e

VPS_USER="mlap"
VPS_HOST="103.1.236.14"
VPS_DIR="/opt/fast-platform"

echo -e "\033[0;36m🚀 Starting Dev Synchronization to VPS ($VPS_HOST)...\033[0m"

# 1. Sync files via Rsync
rsync -avz --no-o --no-g \
  --exclude '.git/' \
  --exclude 'node_modules/' \
  --exclude '.venv/' \
  --exclude 'backups/' \
  --exclude '.env' \
  --exclude 'logs/' \
  --exclude '.pytest_cache/' \
  --exclude '__pycache__/' \
  --exclude 'vad.slice' \
  --exclude 'kehoach.txt' \
  -e "ssh -o StrictHostKeyChecking=no" \
  ./ "$VPS_USER@$VPS_HOST:$VPS_DIR/"

echo -e "\033[0;32m✅ Files synced successfully!\033[0m"

# 2. Ask to restart backend services on the VPS
read -p "Do you want to restart backend services on the VPS? (y/N): " confirm
if [[ "$confirm" =~ ^[Yy]$ ]]; then
  echo -e "\033[0;36m🔄 Restarting backend services on the VPS...\033[0m"
  ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_HOST" "cd $VPS_DIR && ./xohi.sh restart"
  echo -e "\033[0;32m✨ Services restarted successfully!\033[0m"
fi
