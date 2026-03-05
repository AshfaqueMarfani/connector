/// App notification model.
class AppNotification {
  final String id;
  final String notificationType;
  final String title;
  final String body;
  final Map<String, dynamic> data;
  final bool isRead;
  final DateTime? readAt;
  final DateTime createdAt;

  const AppNotification({
    required this.id,
    required this.notificationType,
    required this.title,
    required this.body,
    this.data = const {},
    this.isRead = false,
    this.readAt,
    required this.createdAt,
  });

  factory AppNotification.fromJson(Map<String, dynamic> json) {
    return AppNotification(
      id: json['id'] as String,
      notificationType: json['notification_type'] as String? ?? '',
      title: json['title'] as String? ?? '',
      body: json['body'] as String? ?? '',
      data: json['data'] as Map<String, dynamic>? ?? {},
      isRead: json['is_read'] as bool? ?? false,
      readAt: json['read_at'] != null
          ? DateTime.parse(json['read_at'] as String)
          : null,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  /// Create from WebSocket notification event.
  factory AppNotification.fromWs(Map<String, dynamic> json) {
    return AppNotification(
      id: json['notification_id'] as String? ?? '',
      notificationType: json['notification_type'] as String? ?? '',
      title: json['title'] as String? ?? '',
      body: json['body'] as String? ?? '',
      data: json['data'] as Map<String, dynamic>? ?? {},
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : DateTime.now(),
    );
  }

  bool get isConnectionRequest => notificationType == 'connection_request';
  bool get isConnectionAccepted => notificationType == 'connection_accepted';
  bool get isNewMessage => notificationType == 'new_message';
  bool get isMatchAlert => notificationType == 'match_alert';
}
