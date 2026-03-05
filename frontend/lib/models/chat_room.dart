import 'user.dart';

/// Chat room model.
class ChatRoom {
  final String id;
  final List<User> participants;
  final bool isActive;
  final Message? lastMessage;
  final int unreadCount;
  final DateTime createdAt;
  final DateTime updatedAt;

  const ChatRoom({
    required this.id,
    required this.participants,
    this.isActive = true,
    this.lastMessage,
    this.unreadCount = 0,
    required this.createdAt,
    required this.updatedAt,
  });

  factory ChatRoom.fromJson(Map<String, dynamic> json) {
    return ChatRoom(
      id: json['id'] as String,
      participants: (json['participants'] as List?)
              ?.map((p) => User.fromRef(p as Map<String, dynamic>))
              .toList() ??
          [],
      isActive: json['is_active'] as bool? ?? true,
      lastMessage: json['last_message'] != null
          ? Message.fromJson(json['last_message'] as Map<String, dynamic>)
          : null,
      unreadCount: json['unread_count'] as int? ?? 0,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  /// Get the other participant (not the current user).
  User? otherParticipant(String currentUserId) {
    try {
      return participants.firstWhere((p) => p.id != currentUserId);
    } catch (_) {
      return participants.isNotEmpty ? participants.first : null;
    }
  }
}

/// Chat message model.
class Message {
  final String id;
  final String roomId;
  final User sender;
  final String messageType;
  final String content;
  final bool isRead;
  final DateTime? readAt;
  final DateTime createdAt;

  const Message({
    required this.id,
    required this.roomId,
    required this.sender,
    this.messageType = 'text',
    required this.content,
    this.isRead = false,
    this.readAt,
    required this.createdAt,
  });

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      id: json['id'] as String,
      roomId: json['room'] as String? ?? '',
      sender: User.fromRef(json['sender'] as Map<String, dynamic>),
      messageType: json['message_type'] as String? ?? 'text',
      content: json['content'] as String? ?? '',
      isRead: json['is_read'] as bool? ?? false,
      readAt: json['read_at'] != null
          ? DateTime.parse(json['read_at'] as String)
          : null,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  /// Create from WebSocket message.
  factory Message.fromWs(Map<String, dynamic> json) {
    return Message(
      id: json['message_id'] as String? ?? '',
      roomId: '',
      sender: User(
        id: json['sender_id'] as String? ?? '',
        email: '',
        fullName: json['sender_name'] as String? ?? '',
        accountType: 'individual',
        dateJoined: DateTime.now(),
      ),
      messageType: json['message_type'] as String? ?? 'text',
      content: json['content'] as String? ?? '',
      createdAt: json['timestamp'] != null
          ? DateTime.parse(json['timestamp'] as String)
          : DateTime.now(),
    );
  }

  bool get isLocation => messageType == 'location';
  bool get isSystem => messageType == 'system';
}
