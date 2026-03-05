import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../config/api_config.dart';
import '../core/api/api_client.dart';
import '../core/storage/secure_storage.dart';
import '../models/user.dart';

/// Manages authentication state: login, register, token persistence, logout.
class AuthProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient();

  User? _user;
  bool _isLoading = false;
  String? _error;

  User? get user => _user;
  bool get isAuthenticated => _user != null;
  bool get isLoading => _isLoading;
  String? get error => _error;
  String get userId => _user?.id ?? '';

  /// Try to restore session from stored tokens.
  Future<void> tryAutoLogin() async {
    final token = await SecureStorage.getAccessToken();
    if (token == null) return;

    _isLoading = true;
    notifyListeners();

    try {
      final response = await _api.get(ApiConfig.me);
      _user = User.fromJson(response.data['data'] ?? response.data);
      _error = null;
    } on DioException catch (e) {
      // Token expired or invalid
      if (e.response?.statusCode == 401) {
        await SecureStorage.clearAll();
      }
      _user = null;
    } catch (_) {
      _user = null;
    }

    _isLoading = false;
    notifyListeners();
  }

  /// Register a new account.
  Future<bool> register({
    required String email,
    required String fullName,
    required String password,
    required String passwordConfirm,
    required String accountType,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      await _api.post(ApiConfig.register, data: {
        'email': email,
        'full_name': fullName,
        'password': password,
        'password_confirm': passwordConfirm,
        'account_type': accountType,
        'eula_accepted': true,
      });

      _isLoading = false;
      notifyListeners();
      return true;
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  /// Login with email/password. Returns true on success.
  Future<bool> login({
    required String email,
    required String password,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _api.post(ApiConfig.login, data: {
        'email': email,
        'password': password,
      });

      final data = response.data['data'] as Map<String, dynamic>;
      final accessToken = data['access'] as String;
      final refreshToken = data['refresh'] as String;
      final userData = data['user'] as Map<String, dynamic>;

      await SecureStorage.saveTokens(
        access: accessToken,
        refresh: refreshToken,
      );
      await SecureStorage.setUserId(userData['id'] as String);

      _user = User.fromJson(userData);
      _error = null;
      _isLoading = false;
      notifyListeners();
      return true;
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  /// Logout and clear all stored data.
  Future<void> logout() async {
    await SecureStorage.clearAll();
    _user = null;
    _error = null;
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
