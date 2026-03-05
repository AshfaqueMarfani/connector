#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Connector — Development Setup Script
# Usage: chmod +x scripts/setup_dev.sh && ./scripts/setup_dev.sh
# ═══════════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════════"
echo "  Connector — Development Environment Setup"
echo "═══════════════════════════════════════════════════════"
echo ""

# ── Check prerequisites ──────────────────────────────────────────
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required. Install from https://docker.com"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || command -v docker compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required."; exit 1; }

echo "✅ Docker found"

# ── Backend setup ────────────────────────────────────────────────
echo ""
echo "── Setting up backend... ──"

cd backend

if [ ! -f .env ]; then
    echo "  Creating .env from .env.example..."
    cp .env.example .env
    echo "  ⚠️  Edit backend/.env with your credentials before proceeding!"
else
    echo "  .env already exists — skipping copy"
fi

echo "  Starting Docker services..."
docker-compose up -d --build

echo "  Waiting for services to be healthy..."
sleep 10

echo "  Running database migrations..."
docker-compose run --rm backend python manage.py migrate --noinput

echo "  Seeding test data (20 users around Karachi)..."
docker-compose run --rm backend python manage.py seed_data

echo ""
echo "✅ Backend ready at http://localhost:8000"
echo "   Admin: http://localhost:8000/admin/"
echo "   Credentials: admin@connector.dev / admin123456"

# ── Frontend setup ───────────────────────────────────────────────
echo ""
echo "── Setting up frontend... ──"

cd ../frontend

if command -v flutter >/dev/null 2>&1; then
    echo "  Installing Flutter dependencies..."
    flutter pub get
    echo ""
    echo "✅ Frontend ready — run 'cd frontend && flutter run' to start"
else
    echo "  ⚠️  Flutter not found in PATH. Install from https://flutter.dev"
    echo "     After installing, run: cd frontend && flutter pub get"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Setup complete! Run tests with:"
echo "    Backend:  cd backend && docker-compose run --rm backend python manage.py test"
echo "    Frontend: cd frontend && flutter test"
echo "═══════════════════════════════════════════════════════"
