# 📍 Location Handling & App Store Compliance
**CRITICAL:** Apple and Google will instantly reject the app if location permissions and data exposure are handled incorrectly. All development must adhere to the following rules:

## 1. Location Exposure Logic
* **Private Profiles (Individuals):** * Must NEVER broadcast exact GPS coordinates publicly.
    * Map renders an *estimated* location (obfuscated by adding slight randomization to the coordinate) or a general "zone" radius.
    * Exact location is ONLY unlocked and shared in the P2P chat after a connection request is explicitly accepted by both parties.
* **Public Profiles (Businesses / NGOs):**
    * Rendered with exact GPS coordinates (Pinpoint accuracy) on the public map.

## 2. Background vs. Foreground Tracking
* **Default State:** Location is ONLY updated when the app is in the foreground (active on screen). 
* **Background State:** Background location tracking is strictly disabled by default. 
* **Opt-In Tracking:** Users can explicitly toggle "Live Tracking" in their settings for specific use cases (e.g., traveling to a service job). The app must display a persistent notification when this is active to comply with Android/iOS OS rules.

## 3. OS Permission Flow
1. Ask for `ACCESS_COARSE_LOCATION` first.
2. Only ask for `ACCESS_FINE_LOCATION` when the user interacts with the map.
3. Provide a clear, in-app UI explaining *why* the location is needed before triggering the OS prompt.