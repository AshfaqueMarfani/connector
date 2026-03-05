import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../config/api_config.dart';
import '../core/api/api_client.dart';
import '../core/api/websocket_client.dart';
import '../models/notification.dart';
import 'auth_provider.dart';

/// Manages notifications: fetch, mark read, real-time via WebSocket.
class NotificationProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient();
  AuthProvider? _auth;

  void updateAuth(AuthProvider auth) {
    final wasNull = _auth == null;
    _auth = auth;
    // Auto-connect WS when auth becomes available
    if (wasNull && auth.isAuthenticated) {
      connectWebSocket();
    } else if (!auth.isAuthenticated) {
      disconnectWebSocket();
    }
  }

  List<AppNotification> _notifications = [];
  int _unreadCount = 0;
  bool _isLoading = false;
  String? _error;
  WsClient? _wsClient;

  List<AppNotification> get notifications => _notifications;
  int get unreadCount => _unreadCount;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// Fetch paginated notifications.
  Future<void> fetchNotifications({bool unreadOnly = false}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final params = <String, dynamic>{};
      if (unreadOnly) params['unread_only'] = 'true';

      final response = await _api.get(
        ApiConfig.notifications,
        queryParameters: params,
      );
      final results =
          (response.data['results'] ?? response.data['data'] ?? []) as List;
      _notifications = results
          .map((n) =>
              AppNotification.fromJson(n as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
    }

    _isLoading = false;
    notifyListeners();
  }

  /// Fetch unread count.
  Future<void> fetchUnreadCount() async {
    try {
      final response = await _api.get(ApiConfig.notificationsUnreadCount);
      final data = response.data['data'] ?? response.data;
      _unreadCount = data['unread_count'] as int? ?? 0;
      notifyListeners();
    } on DioException {
      // non-critical
    }
  }

  /// Mark a single notification as read.
  Future<void> markAsRead(String notificationId) async {
    try {
      await _api.post(ApiConfig.notificationRead(notificationId));
      final idx = _notifications.indexWhere((n) => n.id == notificationId);
      if (idx != -1) {
        _notifications[idx] = AppNotification(
          id: _notifications[idx].id,
          notificationType: _notifications[idx].notificationType,
          title: _notifications[idx].title,
          body: _notifications[idx].body,
          data: _notifications[idx].data,
          isRead: true,
          readAt: DateTime.now(),
          createdAt: _notifications[idx].createdAt,
        );
        _unreadCount = (_unreadCount - 1).clamp(0, 999);
        notifyListeners();
      }
    } on DioException {
      // non-critical
    }
  }

  /// Mark all notifications as read.
  Future<void> markAllAsRead() async {
    try {
      await _api.post(ApiConfig.notificationsReadAll);
      _unreadCount = 0;
      for (var i = 0; i < _notifications.length; i++) {
        if (!_notifications[i].isRead) {
          _notifications[i] = AppNotification(
            id: _notifications[i].id,
            notificationType: _notifications[i].notificationType,
            title: _notifications[i].title,
            body: _notifications[i].body,
            data: _notifications[i].data,
            isRead: true,
            readAt: DateTime.now(),
            createdAt: _notifications[i].createdAt,
          );
        }
      }
      notifyListeners();
    } on DioException {
      // non-critical
    }
  }

  /// Connect to the notifications WebSocket.
  Future<void> connectWebSocket() async {
    await _wsClient?.disconnect();

    _wsClient = WsClient.notifications(
      onMessage: _handleWsNotification,
      onConnected: () => notifyListeners(),
      onDisconnected: () => notifyListeners(),
    );

    await _wsClient!.connect();
  }

  void _handleWsNotification(Map<String, dynamic> data) {
    final type = data['type'] as String? ?? '';

    if (type.startsWith('notification')) {
      final notification = AppNotification.fromWs(data);
      _notifications.insert(0, notification);
      _unreadCount++;
      notifyListeners();
    }
  }

  Future<void> disconnectWebSocket() async {
    await _wsClient?.disconnect();
    _wsClient = null;
  }

  @override
  void dispose() {
    _wsClient?.disconnect();
    super.dispose();
  }
}
