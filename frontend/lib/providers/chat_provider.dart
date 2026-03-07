import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../config/api_config.dart';
import '../core/api/api_client.dart';
import '../core/api/websocket_client.dart';
import '../models/chat_room.dart';
import 'auth_provider.dart';

/// Manages chat rooms, messages, and real-time WebSocket communication.
class ChatProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient();
  AuthProvider? _auth;

  void updateAuth(AuthProvider auth) => _auth = auth;

  List<ChatRoom> _rooms = [];
  List<Message> _messages = [];
  bool _isLoading = false;
  String? _error;
  WsClient? _wsClient;
  // ignore: unused_field
  String? _activeRoomId;
  bool _isOtherTyping = false;

  List<ChatRoom> get rooms => _rooms;
  List<Message> get messages => _messages;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isConnected => _wsClient?.isConnected ?? false;
  bool get isOtherTyping => _isOtherTyping;

  /// Fetch all chat rooms.
  Future<void> fetchRooms() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _api.get(ApiConfig.chatRooms);
      final results =
          (response.data['results'] ?? response.data['data'] ?? []) as List;
      _rooms = results
          .map((r) => ChatRoom.fromJson(r as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
    }

    _isLoading = false;
    notifyListeners();
  }

  /// Fetch messages for a specific room.
  Future<void> fetchMessages(String roomId) async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await _api.get(ApiConfig.chatMessages(roomId));
      final results =
          (response.data['results'] ?? response.data['data'] ?? []) as List;
      _messages = results
          .map((m) => Message.fromJson(m as Map<String, dynamic>))
          .toList()
          .reversed
          .toList();
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
    }

    _isLoading = false;
    notifyListeners();
  }

  /// Connect to a chat room's WebSocket.
  Future<void> connectToRoom(String roomId) async {
    _activeRoomId = roomId;
    await _wsClient?.disconnect();

    _wsClient = WsClient.chat(
      roomId: roomId,
      onMessage: _handleWsMessage,
      onConnected: () {
        notifyListeners();
      },
      onDisconnected: () {
        notifyListeners();
      },
    );

    await _wsClient!.connect();
  }

  /// Handle incoming WebSocket messages.
  void _handleWsMessage(Map<String, dynamic> data) {
    final type = data['type'] as String? ?? '';

    switch (type) {
      case 'chat.message':
      case 'chat.location':
        final message = Message.fromWs(data);
        _messages.add(message);
        _isOtherTyping = false;
        notifyListeners();
        break;
      case 'chat.typing':
        final userId = data['user_id'] as String?;
        if (userId != _auth?.userId) {
          _isOtherTyping = data['is_typing'] as bool? ?? false;
          notifyListeners();
        }
        break;
      case 'chat.read':
        final messageId = data['message_id'] as String?;
        if (messageId != null) {
          final idx = _messages.indexWhere((m) => m.id == messageId);
          if (idx != -1) {
            notifyListeners();
          }
        }
        break;
      case 'user.presence':
        notifyListeners();
        break;
    }
  }

  /// Send a text message via WebSocket.
  void sendMessage(String content) {
    _wsClient?.send({
      'type': 'chat.message',
      'content': content,
    });
  }

  /// Send typing indicator.
  void sendTyping(bool isTyping) {
    _wsClient?.send({
      'type': 'chat.typing',
      'is_typing': isTyping,
    });
  }

  /// Share location in chat.
  void sendLocation(double latitude, double longitude) {
    _wsClient?.send({
      'type': 'chat.location',
      'latitude': latitude,
      'longitude': longitude,
    });
  }

  /// Mark a message as read via WebSocket.
  void markMessageRead(String messageId) {
    _wsClient?.send({
      'type': 'chat.read',
      'message_id': messageId,
    });
  }

  /// Mark all messages in a room as read via REST.
  Future<void> markRoomRead(String roomId) async {
    try {
      await _api.post(ApiConfig.chatMarkRead(roomId));
    } on DioException {
      // non-critical
    }
  }

  /// Send a message via REST (fallback).
  Future<bool> sendMessageRest(String roomId, String content) async {
    try {
      final response = await _api.post(
        ApiConfig.chatSendMessage(roomId),
        data: {'content': content},
      );
      final message =
          Message.fromJson(response.data['data'] ?? response.data);
      _messages.add(message);
      notifyListeners();
      return true;
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
      notifyListeners();
      return false;
    }
  }

  /// Disconnect from current room.
  Future<void> disconnectFromRoom() async {
    await _wsClient?.disconnect();
    _wsClient = null;
    _activeRoomId = null;
    _isOtherTyping = false;
    _messages.clear();
    notifyListeners();
  }

  @override
  void dispose() {
    _wsClient?.disconnect();
    super.dispose();
  }
}
