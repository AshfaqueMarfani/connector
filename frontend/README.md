# Connector - Flutter Frontend

## Prerequisites

1. **Flutter SDK** 3.16+ installed and in PATH
2. **Android Studio** (for Android) with Android SDK 34
3. **Xcode** 15+ (for iOS, macOS only)
4. **Chrome** (for web development)
5. Backend running on `localhost:8000` (see `../backend/`)

## Quick Start

```bash
cd frontend

# IMPORTANT: Re-generate platform files with Flutter's tooling
flutter create --project-name connector_app --org com.connector .

# Install dependencies
flutter pub get

# Run on connected device or emulator
flutter run

# Run on web
flutter run -d chrome

# Run on Windows desktop
flutter run -d windows
```

## First-Time Setup

After cloning, you MUST run `flutter create .` to regenerate platform-specific
files that can't be fully version-controlled (Xcode project, Gradle wrapper
binaries, etc.). This will NOT overwrite your Dart source code.

### Android Configuration

The `android/app/src/main/AndroidManifest.xml` already includes:
- `ACCESS_FINE_LOCATION` / `ACCESS_COARSE_LOCATION` for geolocation
- `ACCESS_BACKGROUND_LOCATION` for live tracking
- `CAMERA` for avatar photo capture
- `INTERNET` for API & WebSocket connectivity

**Min SDK:** 21 (Android 5.0)

### iOS Configuration

The `ios/Runner/Info.plist` already includes:
- `NSLocationWhenInUseUsageDescription`
- `NSLocationAlwaysAndWhenInUseUsageDescription`
- `NSCameraUsageDescription`
- `NSPhotoLibraryUsageDescription`

**Min iOS:** 13.0

### Optional: Custom Fonts

To enable the Poppins font family:
1. Download Poppins from [Google Fonts](https://fonts.google.com/specimen/Poppins)
2. Place `.ttf` files in `assets/fonts/`
3. Uncomment the `fonts:` section in `pubspec.yaml`

## Architecture

```
lib/
├── main.dart              # Entry point, MultiProvider setup
├── app.dart               # MaterialApp.router with auto-login
├── config/
│   ├── api_config.dart    # All API endpoint constants
│   ├── routes.dart        # GoRouter with auth guards
│   └── theme.dart         # Light/dark Material 3 themes
├── core/
│   ├── api/
│   │   ├── api_client.dart      # Dio singleton with JWT interceptor
│   │   └── websocket_client.dart # Auto-reconnect WebSocket
│   ├── storage/
│   │   └── secure_storage.dart  # JWT token persistence
│   └── utils/
│       └── validators.dart      # Form validation helpers
├── models/                # 8 data models with fromJson
├── providers/             # 9 state providers (ChangeNotifier)
├── screens/               # 15 UI screens across 8 feature areas
│   ├── auth/              # Login, Register
│   ├── home/              # Map view, Bottom nav shell
│   ├── profile/           # Edit profile, Public profile
│   ├── status/            # Create status, Status list
│   ├── chat/              # Chat rooms, Chat, Connection requests
│   ├── notifications/     # Notification list
│   ├── matching/          # AI match suggestions
│   └── settings/          # Settings & blocked users
└── widgets/
    └── common_widgets.dart # Reusable UI components
```

## Backend Connection

By default:
- **Android emulator:** connects to `10.0.2.2:8000` (host machine)
- **iOS simulator / Web / Desktop:** connects to `localhost:8000`

To change, edit `lib/config/api_config.dart`.

## Running Tests

```bash
flutter test
```

## Building for Release

```bash
# Android APK
flutter build apk --release

# iOS (requires macOS + Xcode)
flutter build ios --release

# Web
flutter build web --release

# Windows
flutter build windows --release
```
