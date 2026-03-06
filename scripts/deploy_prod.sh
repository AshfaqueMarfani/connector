#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Connector — Production Deployment Script (social.otaskflow.com / Hostinger)
# Usage: chmod +x scripts/deploy_prod.sh && ./scripts/deploy_prod.sh
#
# Prerequisites:
#   1. Hostinger VPS (Ubuntu 22.04+, 2 GB RAM minimum)
#   2. Docker & Docker Compose installed on the VPS
#   3. DNS A records (in Hostinger DNS Zone Editor):
#        social.otaskflow.com       → 104.248.171.137
#        api.social.otaskflow.com   → 104.248.171.137
#   4. .env.production configured (see .env.production.template)
# ═══════════════════════════════════════════════════════════════════

set -e

DOMAIN="social.otaskflow.com"
API_DOMAIN="api.social.otaskflow.com"
EMAIL="support@otaskflow.com"   # Let's Encrypt registration email

# Use modern "docker compose" plugin syntax (fallback to docker-compose if available)
if docker compose version &>/dev/null; then
    DC="docker compose"
else
    DC="docker-compose"
fi

echo "═══════════════════════════════════════════════════════"
echo "  Connector — Production Deployment (social.otaskflow.com)"
echo "  Target: Hostinger VPS"
echo "═══════════════════════════════════════════════════════"
echo ""

cd backend

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

# ── Ensure Docker volumes exist ──────────────────────────────────
docker volume create --name=connector_certbot_conf 2>/dev/null || true
docker volume create --name=connector_certbot_www 2>/dev/null || true

# ── SSL Certificate (Let's Encrypt via Certbot) ─────────────────
if [ ! -d "/etc/letsencrypt/live/$API_DOMAIN" ] && ! docker volume inspect connector_certbot_conf | grep -q "CreatedAt" 2>/dev/null; then
    echo ""
    echo "🔒 Obtaining initial SSL certificate from Let's Encrypt..."
    echo "   Ensure DNS A records point to this server BEFORE continuing."
    echo ""

    # Start nginx temporarily for ACME challenge (HTTP only)
    $DC -f docker-compose.prod.yml up -d nginx

    # Request certificate
    $DC -f docker-compose.prod.yml run --rm certbot certbot certonly \
        --webroot \
        -w /var/www/certbot \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        -d "$API_DOMAIN" \
        -d "$DOMAIN"

    # Stop nginx so it restarts with SSL config
    $DC -f docker-compose.prod.yml stop nginx
    echo "✅ SSL certificate obtained"
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

echo ""
echo "Running database migrations..."
$DC -f docker-compose.prod.yml run --rm backend python manage.py migrate --noinput

echo ""
echo "Collecting static files..."
$DC -f docker-compose.prod.yml run --rm backend python manage.py collectstatic --noinput

# ── Health check ─────────────────────────────────────────────────
echo ""
echo "Running health check..."
HTTP_STATUS=$(curl -sk -o /dev/null -w "%{http_code}" "https://$API_DOMAIN/api/v1/health/" 2>/dev/null || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Health check passed (HTTP 200)"
else
    echo "⚠️  Health check returned HTTP $HTTP_STATUS"
    echo "   Check logs: $DC -f docker-compose.prod.yml logs backend"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✅  Production deployment complete!"
echo ""
echo "  Domain:    https://$DOMAIN"
echo "  API:       https://$API_DOMAIN"
echo ""
echo "  Services:"
echo "    Nginx:     https://$API_DOMAIN (port 80→443)"
echo "    Health:    https://$API_DOMAIN/api/v1/health/"
echo "    Admin:     https://$API_DOMAIN/admin/"
echo ""
echo "  SSL:       Let's Encrypt (auto-renews via Certbot container)"
echo ""
echo "  Management:"
echo "    Logs:      $DC -f docker-compose.prod.yml logs -f"
echo "    Stop:      $DC -f docker-compose.prod.yml down"
echo "    Restart:   $DC -f docker-compose.prod.yml restart"
echo "    SSL renew: $DC -f docker-compose.prod.yml run --rm certbot certbot renew"
echo "═══════════════════════════════════════════════════════"
