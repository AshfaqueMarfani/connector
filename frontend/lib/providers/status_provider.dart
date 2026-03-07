import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../config/api_config.dart';
import '../core/api/api_client.dart';
import '../models/status.dart';
import 'auth_provider.dart';

/// Manages user status broadcasts (needs & offers).
class StatusProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient();
  // ignore: unused_field
  AuthProvider? _auth;

  void updateAuth(AuthProvider auth) => _auth = auth;

  List<Status> _statuses = [];
  bool _isLoading = false;
  String? _error;

  List<Status> get statuses => _statuses;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// Fetch the current user's statuses.
  Future<void> fetchMyStatuses() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _api.get(ApiConfig.statusList);
      final results =
          (response.data['results'] ?? response.data['data']?['results'] ?? [])
              as List;
      _statuses =
          results.map((s) => Status.fromJson(s as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
    }

    _isLoading = false;
    notifyListeners();
  }

  /// Create a new need or offer status.
  Future<bool> createStatus({
    required String statusType,
    required String text,
    required String urgency,
    DateTime? expiresAt,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final data = <String, dynamic>{
        'status_type': statusType,
        'text': text,
        'urgency': urgency,
      };
      if (expiresAt != null) {
        data['expires_at'] = expiresAt.toIso8601String();
      }

      final response = await _api.post(ApiConfig.statusCreate, data: data);
      final newStatus =
          Status.fromJson(response.data['data'] ?? response.data);
      _statuses.insert(0, newStatus);
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

  /// Deactivate a status.
  Future<bool> deactivateStatus(String statusId) async {
    try {
      await _api.patch(ApiConfig.statusDeactivate(statusId));
      _statuses.removeWhere((s) => s.id == statusId);
      notifyListeners();
      return true;
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
      notifyListeners();
      return false;
    }
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
