#!/bin/bash
set -e

# Neural Bootstrapper V1.0
echo "🚀 [Trinity Boot] Initializing system..."

# R1.5: Wait for Database to be ready
if [ -n "$DATABASE_URL" ]; then
    echo "📡 [Trinity Boot] Waiting for metadata node (DB)..."
    # Extract host and port from DATABASE_URL
    # Format: postgresql+asyncpg://user:pass@host:port/dbname
    DB_HOST=$(echo $DATABASE_URL | sed -e 's|.*@||' -e 's|/.*||' -e 's|:.*||')
    DB_PORT=$(echo $DATABASE_URL | sed -e 's|.*@||' -e 's|/.*||' -e 's|.*:||' | grep -E '^[0-9]+$' || echo "5432")
    
    # R1.5 Ultra-Lean Check: Use bash built-ins instead of curl
    until (echo > /dev/tcp/$DB_HOST/$DB_PORT) > /dev/null 2>&1; do
      echo "⏳ [Trinity Boot] Metadata node at $DB_HOST:$DB_PORT is offline - sleeping..."
      sleep 2
    done
    echo "✅ [Trinity Boot] Metadata node is online."
fi

# R4.1: Synchronize Database Schema
if [ "$SKIP_MIGRATE" != "true" ]; then
    echo "🧬 [Trinity Boot] Synchronizing neural schema (Alembic)..."
    /opt/venv/bin/alembic -c backend/alembic.ini upgrade head || echo "⚠️ Migration failed, but proceeding..."
else
    echo "⏭️ [Trinity Boot] Skipping migration (Already synced by XOHI OS)."
fi

# R82: Start Litestar Application via Uvicorn (CTO Elite Mode)
if [ "$#" -eq 0 ]; then
    echo "⚡ [Trinity Boot] Igniting Litestar Engine (Uvicorn Recycling)..."
    exec /opt/venv/bin/uvicorn backend.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --http h11 \
        --limit-max-requests 500 \
        --limit-concurrency 15 \
        --timeout-keep-alive 5 
else
    echo "⚡ [Trinity Boot] Executing custom command: $@"
    exec "$@"
fi
