import 'dart:io' show Platform;

/// API and app configuration constants.
class ApiConfig {
  ApiConfig._();

  // ── Environment toggle ───────────────────────────────────────────
  // Set to true for production builds pointing to social.otaskflow.com
  static const bool _isProduction = bool.fromEnvironment(
    'PRODUCTION',
    defaultValue: false,
  );

  // ── Production ───────────────────────────────────────────
  static const String _productionHost = 'api.social.otaskflow.com';
  static const String _productionScheme = 'https';
  static const String _productionWsScheme = 'wss';

  // ── Development ──────────────────────────────────────────────────
  static const String _androidHost = '10.0.2.2:8000'; // Android emulator → host
  static const String _defaultHost = 'localhost:8000'; // iOS / Web / Desktop

  /// Resolved base URLs (protocol-aware)
  static String get baseUrl => _isProduction
      ? '$_productionScheme://$_productionHost'
      : 'http://$_androidHost';
  static String get iosBaseUrl => _isProduction
      ? '$_productionScheme://$_productionHost'
      : 'http://$_defaultHost';
  static String get webBaseUrl => _isProduction
      ? '$_productionScheme://$_productionHost'
      : 'http://$_defaultHost';

  /// Resolved host for the current platform.
  static String get _currentHost {
    if (_isProduction) return _productionHost;
    try {
      if (Platform.isAndroid) return _androidHost;
    } catch (_) {}
    return _defaultHost;
  }

  /// WebSocket scheme
  static String get _wsScheme => _isProduction ? _productionWsScheme : 'ws';

  /// REST endpoints
  static const String apiPrefix = '/api/v1';

  // Auth
  static const String register = '$apiPrefix/auth/register/';
  static const String login = '$apiPrefix/auth/login/';
  static const String tokenRefresh = '$apiPrefix/auth/token/refresh/';
  static const String me = '$apiPrefix/auth/me/';

  // Profile
  static const String profileMe = '$apiPrefix/profile/me/';
  static String profileDetail(String id) => '$apiPrefix/profile/$id/';

  // Location
  static const String locationUpdate = '$apiPrefix/location/update/';
  static const String locationMe = '$apiPrefix/location/me/';
  static const String exploreNearby = '$apiPrefix/explore/nearby/';

  // Status
  static const String statusCreate = '$apiPrefix/status/';
  static const String statusList = '$apiPrefix/status/list/';
  static String statusDeactivate(String id) =>
      '$apiPrefix/status/$id/deactivate/';

  // Moderation
  static const String blockCreate = '$apiPrefix/moderation/block/';
  static const String blockList = '$apiPrefix/moderation/blocks/';
  static String unblock(String blockedId) =>
      '$apiPrefix/moderation/block/$blockedId/';
  static const String reportCreate = '$apiPrefix/moderation/report/';
  static const String reportList = '$apiPrefix/moderation/reports/';

  // Chat & Connections
  static const String connectionRequest =
      '$apiPrefix/chat/connections/request/';
  static const String connectionList = '$apiPrefix/chat/connections/';
  static String connectionAccept(String id) =>
      '$apiPrefix/chat/connections/$id/accept/';
  static String connectionDecline(String id) =>
      '$apiPrefix/chat/connections/$id/decline/';
  static String connectionCancel(String id) =>
      '$apiPrefix/chat/connections/$id/cancel/';
  static const String chatRooms = '$apiPrefix/chat/rooms/';
  static String chatRoomDetail(String roomId) =>
      '$apiPrefix/chat/rooms/$roomId/';
  static String chatMessages(String roomId) =>
      '$apiPrefix/chat/rooms/$roomId/messages/';
  static String chatSendMessage(String roomId) =>
      '$apiPrefix/chat/rooms/$roomId/messages/send/';
  static String chatMarkRead(String roomId) =>
      '$apiPrefix/chat/rooms/$roomId/read/';

  // Notifications
  static const String notifications = '$apiPrefix/notifications/';
  static String notificationRead(String id) =>
      '$apiPrefix/notifications/$id/read/';
  static const String notificationsReadAll =
      '$apiPrefix/notifications/read-all/';
  static const String notificationsUnreadCount =
      '$apiPrefix/notifications/unread-count/';

  // Matching
  static const String matches = '$apiPrefix/matches/';
  static const String matchesSent = '$apiPrefix/matches/sent/';
  static String matchDismiss(String id) => '$apiPrefix/matches/$id/dismiss/';
  static const String aiGenerateTags = '$apiPrefix/ai/generate-tags/';

  /// Platform-aware WebSocket host
  /// WebSocket endpoints
  static String wsChat(String roomId, String token) =>
      '$_wsScheme://$_currentHost/ws/v1/chat/$roomId/?token=$token';
  static String wsNotifications(String token) =>
      '$_wsScheme://$_currentHost/ws/v1/notifications/?token=$token';

  /// Timeouts
  static const Duration connectTimeout = Duration(seconds: 15);
  static const Duration receiveTimeout = Duration(seconds: 15);

  /// Pagination
  static const int defaultPageSize = 20;
}
