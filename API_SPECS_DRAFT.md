# 🔌 Core API Endpoints (Django DRF)

## Authentication
* `POST /api/v1/auth/register/`
* `POST /api/v1/auth/login/` (Returns JWT)

## Profile & Status
* `PATCH /api/v1/profile/me/` (Update skills, interests, privacy toggle)
* `POST /api/v1/status/` (Broadcast a need or offer)

## Geolocation & Matching
* `POST /api/v1/location/update/` (Updates user Point data. Requires JWT)
* `GET /api/v1/explore/nearby/?radius=500&type=ngo,service` (Returns list of obfuscated private users and exact public entities within the PostGIS radius)

## Chat (WebSockets - Django Channels)
* `ws://api/v1/chat/<room_id>/` (Real-time message exchange after connection handshake)