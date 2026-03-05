import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Secure key-value storage for JWT tokens and sensitive data.
class SecureStorage {
  SecureStorage._();

  static late final FlutterSecureStorage _storage;

  static const _accessTokenKey = 'access_token';
  static const _refreshTokenKey = 'refresh_token';
  static const _userIdKey = 'user_id';

  static Future<void> init() async {
    _storage = const FlutterSecureStorage(
      aOptions: AndroidOptions(encryptedSharedPreferences: true),
    );
  }

  // Access Token
  static Future<String?> getAccessToken() =>
      _storage.read(key: _accessTokenKey);

  static Future<void> setAccessToken(String token) =>
      _storage.write(key: _accessTokenKey, value: token);

  // Refresh Token
  static Future<String?> getRefreshToken() =>
      _storage.read(key: _refreshTokenKey);

  static Future<void> setRefreshToken(String token) =>
      _storage.write(key: _refreshTokenKey, value: token);

  // User ID
  static Future<String?> getUserId() => _storage.read(key: _userIdKey);

  static Future<void> setUserId(String id) =>
      _storage.write(key: _userIdKey, value: id);

  // Clear all
  static Future<void> clearAll() => _storage.deleteAll();

  // Store token pair
  static Future<void> saveTokens({
    required String access,
    required String refresh,
  }) async {
    await Future.wait([
      setAccessToken(access),
      setRefreshToken(refresh),
    ]);
  }
}
