# 🛡 Security, UGC, & Moderation

## 1. User-Generated Content (UGC) - MVP Phase
To pass Apple/Google App Store review for UGC apps, the MVP *must* include:
* **EULA:** A strict End User License Agreement that users must accept on signup.
* **Block/Report:** A mandatory UI button on every user profile and chat message allowing users to "Block User" or "Report Content."
* **Backend Moderation:** A basic Django admin dashboard to review reported users and immediately suspend accounts.

## 2. Authentication & Trust
* **Current Phase (MVP):** Standard Email/Password verification (JWT Auth).
* **Next Phase (10k+ Users):** Implementation of specialized KYC (Know Your Customer) workflows for specific service categories (e.g., verifying licenses for electricians or official registration for NGOs).

## 3. Data Protection
* All P2P chat messages must be encrypted in transit (WSS/HTTPS) and stored securely.
* Geospatial data for private users must be decoupled from their primary identifiable data where possible to prevent scraping of user locations.