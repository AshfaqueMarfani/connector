import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart' show VoidCallback;
import 'package:logger/logger.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../../config/api_config.dart';
import '../storage/secure_storage.dart';

final _logger = Logger(printer: PrettyPrinter(methodCount: 0));

/// Manages a WebSocket connection with auto-reconnect.
class WsClient {
  final String Function(String token) _urlBuilder;
  final void Function(Map<String, dynamic> data) onMessage;
  final VoidCallback? onConnected;
  final VoidCallback? onDisconnected;

  WebSocketChannel? _channel;
  StreamSubscription? _subscription;
  Timer? _reconnectTimer;
  Timer? _pingTimer;
  bool _disposed = false;
  bool _isConnected = false;
  int _reconnectAttempts = 0;
  static const int _maxReconnectAttempts = 10;

  bool get isConnected => _isConnected;

  WsClient({
    required String Function(String token) urlBuilder,
    required this.onMessage,
    this.onConnected,
    this.onDisconnected,
  }) : _urlBuilder = urlBuilder;

  /// Chat WebSocket factory
  factory WsClient.chat({
    required String roomId,
    required void Function(Map<String, dynamic>) onMessage,
    VoidCallback? onConnected,
    VoidCallback? onDisconnected,
  }) {
    return WsClient(
      urlBuilder: (token) => ApiConfig.wsChat(roomId, token),
      onMessage: onMessage,
      onConnected: onConnected,
      onDisconnected: onDisconnected,
    );
  }

  /// Notifications WebSocket factory
  factory WsClient.notifications({
    required void Function(Map<String, dynamic>) onMessage,
    VoidCallback? onConnected,
    VoidCallback? onDisconnected,
  }) {
    return WsClient(
      urlBuilder: (token) => ApiConfig.wsNotifications(token),
      onMessage: onMessage,
      onConnected: onConnected,
      onDisconnected: onDisconnected,
    );
  }

  Future<void> connect() async {
    if (_disposed) return;

    final token = await SecureStorage.getAccessToken();
    if (token == null) {
      _logger.w('WS: No token available, skipping connection');
      return;
    }

    try {
      final url = _urlBuilder(token);
      _logger.d('WS: Connecting to $url');

      _channel = WebSocketChannel.connect(Uri.parse(url));
      await _channel!.ready;

      _isConnected = true;
      _reconnectAttempts = 0;
      onConnected?.call();
      _logger.d('WS: Connected');

      _startPing();

      _subscription = _channel!.stream.listen(
        (data) {
          if (_disposed) return;
          try {
            final decoded = jsonDecode(data as String) as Map<String, dynamic>;
            onMessage(decoded);
          } catch (e) {
            _logger.e('WS: Failed to decode message: $e');
          }
        },
        onError: (error) {
          _logger.e('WS: Stream error: $error');
          _handleDisconnect();
        },
        onDone: () {
          _logger.d('WS: Connection closed (code: ${_channel?.closeCode})');
          _handleDisconnect();
        },
        cancelOnError: false,
      );
    } catch (e) {
      _logger.e('WS: Connection failed: $e');
      _handleDisconnect();
    }
  }

  void send(Map<String, dynamic> data) {
    if (_channel != null && _isConnected) {
      _channel!.sink.add(jsonEncode(data));
    } else {
      _logger.w('WS: Tried to send while disconnected');
    }
  }

  void _startPing() {
    _pingTimer?.cancel();
    _pingTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      if (_isConnected) {
        send({'type': 'ping'});
      }
    });
  }

  void _handleDisconnect() {
    _isConnected = false;
    _pingTimer?.cancel();
    onDisconnected?.call();

    if (!_disposed && _reconnectAttempts < _maxReconnectAttempts) {
      final delay = Duration(
        seconds: (_reconnectAttempts + 1) * 2, // Exponential backoff
      );
      _logger.d('WS: Reconnecting in ${delay.inSeconds}s '
          '(attempt ${_reconnectAttempts + 1})');

      _reconnectTimer?.cancel();
      _reconnectTimer = Timer(delay, () {
        _reconnectAttempts++;
        connect();
      });
    }
  }

  Future<void> disconnect() async {
    _disposed = true;
    _reconnectTimer?.cancel();
    _pingTimer?.cancel();
    _subscription?.cancel();

    if (_channel != null) {
      await _channel!.sink.close();
      _channel = null;
    }
    _isConnected = false;
    _logger.d('WS: Disconnected');
  }
}
