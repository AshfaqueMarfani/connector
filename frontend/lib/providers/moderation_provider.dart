import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../config/api_config.dart';
import '../core/api/api_client.dart';
import 'auth_provider.dart';

/// Manages block and report functionality.
class ModerationProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient();
  // ignore: unused_field
  AuthProvider? _auth;

  void updateAuth(AuthProvider auth) => _auth = auth;

  List<Map<String, dynamic>> _blockedUsers = [];
  bool _isLoading = false;
  String? _error;

  List<Map<String, dynamic>> get blockedUsers => _blockedUsers;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// Fetch list of blocked users.
  Future<void> fetchBlockedUsers() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _api.get(ApiConfig.blockList);
      final results =
          (response.data['results'] ?? response.data['data'] ?? []) as List;
      _blockedUsers =
          results.map((b) => b as Map<String, dynamic>).toList();
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
    }

    _isLoading = false;
    notifyListeners();
  }

  /// Block a user.
  Future<bool> blockUser(String userId, {String? reason}) async {
    try {
      final data = <String, dynamic>{'blocked': userId};
      if (reason != null) data['reason'] = reason;
      await _api.post(ApiConfig.blockCreate, data: data);
      await fetchBlockedUsers();
      return true;
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
      notifyListeners();
      return false;
    }
  }

  /// Unblock a user.
  Future<bool> unblockUser(String userId) async {
    try {
      await _api.delete(ApiConfig.unblock(userId));
      _blockedUsers.removeWhere((b) => b['blocked'] == userId);
      notifyListeners();
      return true;
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
      notifyListeners();
      return false;
    }
  }

  /// Report a user/content.
  Future<bool> reportContent({
    required String reportedUserId,
    required String contentType,
    required String category,
    required String description,
    String? contentId,
  }) async {
    try {
      await _api.post(ApiConfig.reportCreate, data: {
        'reported_user': reportedUserId,
        'content_type': contentType,
        'category': category,
        'description': description,
        if (contentId != null) 'content_id': contentId,
      });
      return true;
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
      notifyListeners();
      return false;
    }
  }

  /// Check if a user is blocked.
  bool isUserBlocked(String userId) {
    return _blockedUsers.any((b) => b['blocked'] == userId);
  }
}
