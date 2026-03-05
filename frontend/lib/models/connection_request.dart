import 'user.dart';

/// Connection request model.
class ConnectionRequest {
  final String id;
  final User fromUser;
  final User toUser;
  final String message;
  final String status; // pending, accepted, declined, cancelled
  final String? chatRoomId;
  final DateTime createdAt;
  final DateTime updatedAt;

  const ConnectionRequest({
    required this.id,
    required this.fromUser,
    required this.toUser,
    this.message = '',
    required this.status,
    this.chatRoomId,
    required this.createdAt,
    required this.updatedAt,
  });

  factory ConnectionRequest.fromJson(Map<String, dynamic> json) {
    return ConnectionRequest(
      id: json['id'] as String,
      fromUser: User.fromRef(json['from_user'] as Map<String, dynamic>),
      toUser: User.fromRef(json['to_user'] as Map<String, dynamic>),
      message: json['message'] as String? ?? '',
      status: json['status'] as String? ?? 'pending',
      chatRoomId: json['chat_room'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  bool get isPending => status == 'pending';
  bool get isAccepted => status == 'accepted';
}
