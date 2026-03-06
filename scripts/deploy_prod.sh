#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Connector — Production Deployment Script (social.otaskflow.com)
# Usage: chmod +x scripts/deploy_prod.sh && ./scripts/deploy_prod.sh
#
# This script deploys alongside an EXISTING nginx + other Django app on the VPS.
# It uses the HOST nginx to route social.otaskflow.com → Connector backend:8001.
#
# Prerequisites:
#   1. VPS (Ubuntu 22.04+) with Docker, Docker Compose, nginx already installed
#   2. DNS A record:  social.otaskflow.com → 104.248.171.137
#   3. .env.production configured (see .env.production.template)
# ═══════════════════════════════════════════════════════════════════

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOMAIN="social.otaskflow.com"
EMAIL="support@otaskflow.com"

# Use modern "docker compose" plugin syntax (fallback to docker-compose if available)
if docker compose version &>/dev/null; then
    DC="docker compose"
else
    DC="docker-compose"
fi

echo "═══════════════════════════════════════════════════════"
echo "  Connector — Production Deployment"
echo "  Subdomain: social.otaskflow.com  (alongside existing VPS apps)"
echo "═══════════════════════════════════════════════════════"
echo ""

cd "$PROJECT_ROOT/backend"

# ── Pre-flight checks ────────────────────────────────────────────
if [ ! -f .env.production ]; then
    echo "❌ .env.production not found!"
    echo "   Copy .env.production.template → .env.production and fill in real values."
    exit 1
fi

if grep -q "CHANGE-ME" .env.production; then
    echo "❌ .env.production contains placeholder values (CHANGE-ME)"
    echo "   Replace all CHANGE-ME values with real production credentials."
    exit 1
fi

echo "✅ Production environment file validated"

# ── Symlink .env so docker-compose can interpolate variables ─────
ln -sf .env.production .env
echo "✅ Linked .env → .env.production for Docker Compose"

# ── Ensure swap exists (GDAL build needs >1 GB) ─────────────────
if [ ! -f /swapfile ]; then
    echo "📦 Creating 2 GB swap file for Docker builds..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "✅ Swap enabled"
else
    sudo swapon /swapfile 2>/dev/null || true
    echo "✅ Swap already configured"
fi

# ── Prepare host directories for static/media ────────────────────
mkdir -p "$PROJECT_ROOT/backend/staticfiles"
mkdir -p "$PROJECT_ROOT/backend/media"

# ── Install host nginx config ────────────────────────────────────
NGINX_CONF="$PROJECT_ROOT/nginx/social.otaskflow.com.conf"
if [ -f "$NGINX_CONF" ]; then
    echo "📦 Installing nginx server block for $DOMAIN..."
    sudo cp "$NGINX_CONF" /etc/nginx/sites-available/social.otaskflow.com
    sudo ln -sf /etc/nginx/sites-available/social.otaskflow.com /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx
    echo "✅ Host nginx configured for $DOMAIN"
else
    echo "⚠️  Nginx config not found at $NGINX_CONF — skipping"
fi

# ── Build & Deploy ───────────────────────────────────────────────
echo ""
echo "Building production images..."
$DC -f docker-compose.prod.yml build

echo ""
echo "Starting production services..."
$DC -f docker-compose.prod.yml up -d

echo ""
echo "Waiting for services to be healthy..."
sleep 20

# ── Health check ─────────────────────────────────────────────────
echo ""
echo "Running health check..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8001/api/v1/health/" 2>/dev/null || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Health check passed (HTTP 200)"
else
    echo "⚠️  Health check returned HTTP $HTTP_STATUS"
    echo "   Check logs: $DC -f docker-compose.prod.yml logs backend"
fi

# ── SSL (Let's Encrypt via host certbot) ─────────────────────────
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo ""
    echo "🔒 To enable HTTPS, run:"
    echo "   sudo certbot --nginx -d $DOMAIN"
    echo ""
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✅  Production deployment complete!"
echo ""
echo "  API (HTTP):  http://$DOMAIN/api/v1/"
echo "  Health:      http://$DOMAIN/api/v1/health/"
echo "  Admin:       http://$DOMAIN/admin/"
echo ""
echo "  Backend:     127.0.0.1:8001 (Docker → Daphne ASGI)"
echo "  Nginx:       Host nginx proxying $DOMAIN → :8001"
echo ""
echo "  Next steps:"
echo "    1. Ensure DNS A record points to this server"
echo "    2. Run: sudo certbot --nginx -d $DOMAIN"
echo "    3. Test: curl https://$DOMAIN/api/v1/health/"
echo ""
echo "  Management:"
echo "    Logs:      $DC -f docker-compose.prod.yml logs -f"
echo "    Stop:      $DC -f docker-compose.prod.yml down"
echo "    Restart:   $DC -f docker-compose.prod.yml restart"
echo "═══════════════════════════════════════════════════════"
