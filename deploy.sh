#!/bin/bash

# Trinity Core V18.0 - Endgame Deployment Script
# Usage: ./deploy.sh

set -e

echo "🚀 Starting Trinity Core V18.0 Deployment..."

# Load APP_DOMAIN for the final message
APP_DOMAIN=$(grep '^APP_DOMAIN=' .env | cut -d '=' -f 2-)

echo "📦 Stopping existing containers..."
docker compose down --remove-orphans

echo "🔨 Building latest images (using cache)..."
docker compose build

echo "✨ Initializing Database & 🌱 Seeding (Unified)..."
docker compose run --rm api sh -c "cd apps/api-gateway && alembic upgrade head && python src/scripts/seed.py"

echo "🔥 Launching Trinity Core in Production Mode..."
docker compose up -d

# Check status
echo "📡 Checking container status..."
docker compose ps

echo "✅ Deployment Successful!"
echo "🌐 Access your platform at: https://${APP_DOMAIN}"
echo "📡 Health Check: https://${APP_DOMAIN}/health"
echo "� Tip: Run 'docker compose logs -f caddy' to monitor SSL status."
