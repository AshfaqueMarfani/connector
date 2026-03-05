import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../config/api_config.dart';
import '../core/api/api_client.dart';
import '../models/connection_request.dart';
import 'auth_provider.dart';

/// Manages connection requests (send, accept, decline, cancel).
class ConnectionProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient();
  AuthProvider? _auth;

  void updateAuth(AuthProvider auth) => _auth = auth;

  List<ConnectionRequest> _requests = [];
  bool _isLoading = false;
  String? _error;

  List<ConnectionRequest> get requests => _requests;
  bool get isLoading => _isLoading;
  String? get error => _error;

  List<ConnectionRequest> get receivedPending => _requests
      .where((r) => r.isPending && r.toUser.id == _auth?.userId)
      .toList();

  List<ConnectionRequest> get sentPending => _requests
      .where((r) => r.isPending && r.fromUser.id == _auth?.userId)
      .toList();

  /// Fetch connection requests with optional filters.
  Future<void> fetchRequests({
    String direction = 'all',
    String? status,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final params = <String, dynamic>{'direction': direction};
      if (status != null) params['status'] = status;

      final response = await _api.get(
        ApiConfig.connectionList,
        queryParameters: params,
      );
      final results =
          (response.data['results'] ?? response.data['data'] ?? []) as List;
      _requests = results
          .map((r) => ConnectionRequest.fromJson(r as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
    }

    _isLoading = false;
    notifyListeners();
  }

  /// Send a connection request to a user.
  Future<bool> sendRequest(String toUserId, {String? message}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final data = <String, dynamic>{'to_user': toUserId};
      if (message != null && message.isNotEmpty) data['message'] = message;

      await _api.post(ApiConfig.connectionRequest, data: data);
      await fetchRequests();
      return true;
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  /// Accept a connection request. Returns the chat room ID if created.
  Future<String?> acceptRequest(String requestId) async {
    try {
      final response =
          await _api.post(ApiConfig.connectionAccept(requestId));
      final data = response.data['data'] ?? response.data;
      await fetchRequests();
      return data['chat_room'] as String?;
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
      notifyListeners();
      return null;
    }
  }

  /// Decline a connection request.
  Future<bool> declineRequest(String requestId) async {
    try {
      await _api.post(ApiConfig.connectionDecline(requestId));
      _requests.removeWhere((r) => r.id == requestId);
      notifyListeners();
      return true;
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
      notifyListeners();
      return false;
    }
  }

  /// Cancel a sent connection request.
  Future<bool> cancelRequest(String requestId) async {
    try {
      await _api.post(ApiConfig.connectionCancel(requestId));
      _requests.removeWhere((r) => r.id == requestId);
      notifyListeners();
      return true;
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
      notifyListeners();
      return false;
    }
  }
}
