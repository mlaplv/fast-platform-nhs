#!/bin/bash
# Cerberus 2026 Infrastructure Test Suite
# Compliance: Elite V2.2 (2GB RAM Limit, Ultra-Lean Architecture)

echo "🚀 Starting Cerberus 2026 Infrastructure Test..."

# 1. Check Services Status
echo "--- Service Status ---"
docker compose ps

# 2. Database & Vector Search Audit
echo "--- DB Vector Extension Test ---"
docker exec fast_platform_db psql -U postgres -d fast_platform -c "SELECT * FROM pg_extension WHERE extname = 'vector';" || echo "❌ pgvector missing!"

# 3. Redis Connectivity Audit
echo "--- Redis Health Audit ---"
docker exec fast_platform_redis redis-cli ping | grep PONG && echo "✅ Redis UP" || echo "❌ Redis DOWN"

# 4. API Health & Migration Audit
echo "--- API Integrity Audit ---"
docker exec fast_platform_api litestar --app backend.main:app routes || echo "❌ API Routes failing!"

# 5. Resource Consumption Audit (R60.1 Compliance)
echo "--- Resource Consumption (2GB Target) ---"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo "✅ Audit Complete."
