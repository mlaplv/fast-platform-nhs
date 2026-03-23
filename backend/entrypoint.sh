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
    
    until curl -s http://$DB_HOST:$DB_PORT > /dev/null 2>&1 || [ $? -eq 52 ] || [ $? -eq 7 ]; do
      echo "⏳ [Trinity Boot] Metadata node at $DB_HOST:$DB_PORT is offline - sleeping..."
      sleep 2
    done
    echo "✅ [Trinity Boot] Metadata node is online."
fi

# R4.1: Synchronize Database Schema
echo "🧬 [Trinity Boot] Synchronizing neural schema (Alembic)..."
alembic -c backend/alembic.ini upgrade head

# R82: Start Litestar Application
echo "⚡ [Trinity Boot] Igniting Litestar Engine..."
exec litestar --app backend.main:app run --port 8000 --host 0.0.0.0 --reload
