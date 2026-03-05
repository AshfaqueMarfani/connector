# 🌍 Connector — Hyperlocal Connection & Service Platform

> A production-ready, cross-platform (iOS/Android) location-based networking and service marketplace. The platform connects nearby individuals, businesses, and NGOs based on real-time needs, skills, and offers within a dynamic geographical radius.

---

## Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Production Deployment](#production-deployment)
- [API Endpoints](#api-endpoints)
- [CI/CD Pipeline](#cicd-pipeline)
- [App Store Compliance](#app-store-compliance)

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐
│   Flutter App    │────▷│   Nginx Proxy    │
│ (iOS / Android)  │     │   (Port 80/443)  │
└─────────────────┘     └──────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
     ┌────────────┐   ┌─────────────┐   ┌───────────┐
     │  Django     │   │  WebSocket  │   │  Static   │
     │  REST API   │   │  (Channels) │   │  Files    │
     │  (Daphne)   │   │  /ws/       │   │  (Nginx)  │
     └─────┬──────┘   └──────┬──────┘   └───────────┘
           │                  │
     ┌─────┼──────────────────┼─────┐
     ▼     ▼                  ▼     ▼
┌──────┐ ┌──────┐      ┌──────┐ ┌──────────┐
│PostGIS│ │Redis │      │Celery│ │Celery    │
│  DB   │ │Cache │      │Worker│ │Beat      │
└──────┘ └──────┘      └──────┘ └──────────┘
```

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| **Frontend** | Flutter / Dart | 3.27.4 / 3.6.2 |
| **Backend** | Django + DRF | 5.1.4 / 3.15.2 |
| **Database** | PostgreSQL + PostGIS | 16 / 3.4 |
| **Real-time** | Django Channels + Redis | 4.2.0 / 7 |
| **Task Queue** | Celery + Redis Broker | 5.4.0 |
| **ASGI Server** | Daphne | 4.1.2 |
| **AI Matching** | OpenAI GPT-4 | via API |
| **Auth** | JWT (SimpleJWT) | 5.4.0 |
| **Reverse Proxy** | Nginx | 1.25 |
| **CI/CD** | GitHub Actions | — |

---

## Project Structure

```
Connector/
├── .github/workflows/
│   └── ci.yml                 # CI/CD pipeline
├── backend/
│   ├── apps/
│   │   ├── accounts/          # Auth, user management, seed data
│   │   ├── profiles/          # Public/private profiles, skills, tags
│   │   ├── locations/         # GPS updates, PostGIS exploration, entity ingestion
│   │   ├── statuses/          # Need/offer broadcasts
│   │   ├── moderation/        # Block, report, admin review
│   │   ├── chat/              # WebSocket chat, connections, notifications
│   │   └── matching/          # AI matching engine, Celery tasks
│   ├── connector_backend/     # Django settings, urls, ASGI, Celery config
│   ├── tests/                 # Backend test suite (105 tests)
│   ├── nginx/                 # Nginx reverse proxy config
│   ├── docker-compose.yml     # Development stack
│   ├── docker-compose.prod.yml # Production stack (with Nginx)
│   ├── Dockerfile             # Development Docker image
│   ├── Dockerfile.prod        # Production multi-stage image
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Development env template
├── frontend/
│   ├── lib/
│   │   ├── config/            # Routes, theme, API config
│   │   ├── core/              # API client, WebSocket, storage, validators
│   │   ├── models/            # 8 data models (user, profile, status, etc.)
│   │   ├── providers/         # 9 state providers (auth, chat, location, etc.)
│   │   ├── screens/           # 15 screens across 8 feature groups
│   │   └── widgets/           # Reusable UI components
│   ├── test/                  # Flutter test suite
│   └── pubspec.yaml           # Flutter dependencies
├── PROJECT_OVERVIEW.md
├── ARCHITECTURE_AND_DATA.md
├── API_SPECS_DRAFT.md
├── SECURITY_AND_UGC.md
└── LOCATION_AND_PRIVACY_TOS.md
```

---

## Prerequisites

- **Docker Desktop** (v24+) with Docker Compose
- **Flutter SDK** (3.16+ / stable channel)
- **Git**

---

## Development Setup

### 1. Clone & Configure

```bash
git clone <repo-url> Connector
cd Connector/backend
cp .env.example .env
# Edit .env with your values (DB credentials, OpenAI key, etc.)
```

### 2. Start Backend Services

```bash
cd backend
docker-compose up -d --build
```

This starts 5 services:
- **PostGIS** database on port `5432`
- **Redis** on port `6379`
- **Django/Daphne** API on port `8000`
- **Celery Worker** (4 concurrent tasks)
- **Celery Beat** (periodic scheduler)

### 3. Initialize Database

```bash
# Apply migrations
docker-compose run --rm backend python manage.py migrate

# Create superuser
docker-compose run --rm backend python manage.py createsuperuser

# Seed test data (20 users around Karachi)
docker-compose run --rm backend python manage.py seed_data
```

**Admin Panel:** http://localhost:8000/admin/
- Default seed admin: `admin@connector.dev` / `admin123456`
- Seed user password: `SeedPassword123!`

### 4. Start Flutter App

```bash
cd frontend
flutter pub get
flutter run
```

The Flutter app auto-detects the backend host:
- **Android emulator:** `10.0.2.2:8000`
- **iOS simulator:** `localhost:8000`
- **Web:** `localhost:8000`

---

## Running Tests

### Backend Tests (105 tests)

```bash
cd backend
docker-compose run --rm backend python manage.py test --verbosity=2
```

### Frontend Tests

```bash
cd frontend
flutter test
```

### Static Analysis

```bash
# Backend
docker-compose run --rm backend flake8 apps/ --max-line-length=120 --exclude=migrations

# Frontend (zero errors required)
flutter analyze --no-fatal-warnings --no-fatal-infos
```

---

## Production Deployment (Hostinger VPS)

### 0. Hostinger VPS Setup

```bash
# Order a VPS from hostinger.pk: Ubuntu 22.04 LTS, 2 GB RAM minimum (4 GB recommended)
# Enable automatic backups

# SSH into the VPS and install Docker
ssh root@104.248.171.137
curl -fsSL https://get.docker.com | sh
apt install -y docker-compose-plugin

# Configure DNS (in Hostinger DNS Zone Editor for otaskflow.com):
#   A record:  social.otaskflow.com       → 104.248.171.137
#   A record:  api.social.otaskflow.com   → 104.248.171.137

# Configure firewall
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP (for ACME + redirect)
ufw allow 443/tcp  # HTTPS
ufw enable
```

### 1. Configure Production Environment

```bash
cd backend
cp .env.production.template .env.production
# Edit .env.production with REAL credentials:
# - Strong DJANGO_SECRET_KEY
# - Production DB_PASSWORD
# - Real OPENAI_API_KEY
# - DJANGO_ALLOWED_HOSTS=api.social.otaskflow.com,social.otaskflow.com,localhost
# - CORS_ALLOWED_ORIGINS=https://social.otaskflow.com,https://api.social.otaskflow.com
```

### 2. SSL Certificates (Automatic via Let's Encrypt)

SSL certificates are managed automatically by the Certbot container.
On first deploy, the deploy script obtains the initial certificate:

```bash
# The deploy script handles initial cert generation:
chmod +x scripts/deploy_prod.sh
./scripts/deploy_prod.sh

# Or manually obtain the initial certificate:
docker-compose -f docker-compose.prod.yml up -d nginx
docker-compose -f docker-compose.prod.yml run --rm certbot certbot certonly \
    --webroot -w /var/www/certbot \
    --email support@otaskflow.com --agree-tos --no-eff-email \
    -d api.social.otaskflow.com -d social.otaskflow.com
docker-compose -f docker-compose.prod.yml restart nginx
```

### 3. Deploy with Production Compose

```bash
cd backend
docker-compose -f docker-compose.prod.yml up -d --build
```

Production stack includes:
- **Nginx** reverse proxy on ports 80/443 with TLS termination
- **Certbot** auto-renewing Let's Encrypt SSL certificates
- **Multi-stage Docker build** (smaller image, non-root user)
- **Health checks** on all services
- **Redis** with memory limits and LRU eviction
- **Isolated Docker network**

### 4. Post-Deployment

```bash
# Apply migrations
docker-compose -f docker-compose.prod.yml run --rm backend python manage.py migrate

# Create admin
docker-compose -f docker-compose.prod.yml run --rm backend python manage.py createsuperuser

# Seed initial data (optional)
docker-compose -f docker-compose.prod.yml run --rm backend python manage.py seed_data

# Ingest third-party entities (optional)
docker-compose -f docker-compose.prod.yml run --rm backend python manage.py ingest_entities sample_entities.json
```

### 5. Health Checks

- **Health:** `GET https://api.social.otaskflow.com/api/v1/health/` — Returns status of DB, Redis, Celery
- **Readiness:** `GET https://api.social.otaskflow.com/api/v1/ready/` — Quick DB-only probe for load balancers

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register/` | Create account |
| `POST` | `/api/v1/auth/login/` | Obtain JWT tokens |
| `POST` | `/api/v1/auth/refresh/` | Refresh access token |
| `POST` | `/api/v1/auth/logout/` | Blacklist refresh token |
| `GET/PATCH` | `/api/v1/profile/me/` | View / update own profile |
| `GET` | `/api/v1/profile/<uuid>/` | View public profile |
| `POST` | `/api/v1/location/update/` | Update GPS position |
| `GET` | `/api/v1/explore/nearby/` | Find nearby users/entities |
| `GET/POST` | `/api/v1/statuses/` | List / create statuses |
| `POST` | `/api/v1/connections/request/` | Send connection request |
| `POST` | `/api/v1/connections/<id>/respond/` | Accept / decline |
| `GET` | `/api/v1/chat/rooms/` | List chat rooms |
| `GET` | `/api/v1/notifications/` | List notifications |
| `GET` | `/api/v1/matching/results/` | AI match results |
| `POST` | `/api/v1/moderation/report/` | Report content |
| `POST` | `/api/v1/moderation/block/` | Block user |
| `GET` | `/api/v1/health/` | Service health check |
| `WS` | `/ws/chat/<room_id>/` | Real-time chat WebSocket |

---

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push to `main` and `develop`:

1. **Backend Tests** — Spins up PostGIS + Redis services, runs flake8/black/isort checks, then 105 Django tests
2. **Flutter Tests** — Installs Flutter, runs `flutter analyze` (zero errors) + `flutter test` with coverage
3. **Docker Build** — Validates production Docker image builds (on `main` branch only)

---

## App Store Compliance

The app implements all requirements for Apple/Google UGC app approval:

- **EULA Screen** — Full Terms of Service accessible from registration (`/eula` route)
- **Block/Report** — Available on every profile and in chat (Block User, Report Content)
- **Moderation Dashboard** — Django admin panel for reviewing reports and suspending accounts
- **Location Privacy** — Private profiles use obfuscated coordinates (200m radius); exact location only shared after mutual connection
- **Permission Flow** — Coarse → Fine location with in-app explanation
- **Background Tracking** — Disabled by default, explicit opt-in with persistent notification

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | — | **Required.** Cryptographic signing key |
| `DJANGO_DEBUG` | `False` | Enable debug mode (dev only) |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |
| `DB_NAME` | `connector_db` | PostgreSQL database name |
| `DB_USER` | `connector_user` | Database username |
| `DB_PASSWORD` | — | **Required.** Database password |
| `DB_HOST` | `localhost` | Database host |
| `DB_PORT` | `5432` | Database port |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for Channels |
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Celery message broker |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/2` | Celery result store |
| `OPENAI_API_KEY` | `""` | OpenAI API key for AI matching |
| `OPENAI_MODEL` | `gpt-4` | OpenAI model name |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | `60` | JWT access token lifetime |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | `7` | JWT refresh token lifetime |
| `LOCATION_OBFUSCATION_RADIUS_METERS` | `200` | Privacy radius for private profiles |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |

---

## License

Proprietary — All rights reserved.
