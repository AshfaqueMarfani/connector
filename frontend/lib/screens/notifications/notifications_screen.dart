import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:timeago/timeago.dart' as timeago;

import '../../models/notification.dart';
import '../../providers/notification_provider.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<NotificationProvider>().fetchNotifications();
    });
  }

  IconData _iconForType(String type) {
    switch (type) {
      case 'connection_request':
        return Icons.person_add;
      case 'connection_accepted':
        return Icons.handshake;
      case 'new_message':
        return Icons.chat_bubble;
      case 'match_found':
        return Icons.auto_awesome;
      case 'status_response':
        return Icons.reply;
      case 'nearby_alert':
        return Icons.location_on;
      default:
        return Icons.notifications;
    }
  }

  Color _colorForType(String type, ThemeData theme) {
    switch (type) {
      case 'connection_request':
        return Colors.blue;
      case 'connection_accepted':
        return Colors.green;
      case 'new_message':
        return Colors.teal;
      case 'match_found':
        return Colors.purple;
      case 'status_response':
        return Colors.orange;
      case 'nearby_alert':
        return Colors.red;
      default:
        return theme.colorScheme.primary;
    }
  }

  void _onTap(AppNotification notif) {
    final provider = context.read<NotificationProvider>();
    if (!notif.isRead) {
      provider.markAsRead(notif.id);
    }

    // Navigate based on type
    final data = notif.data;
    if (notif.notificationType == 'connection_request' ||
        notif.notificationType == 'connection_accepted') {
      context.push('/connections');
    } else if (notif.notificationType == 'new_message' && data['room_id'] != null) {
      context.push('/chat/${data['room_id']}');
    } else if (notif.notificationType == 'match_found') {
      context.go('/matches');
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<NotificationProvider>();
    final theme = Theme.of(context);
    final notifications = provider.notifications;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        actions: [
          if (provider.unreadCount > 0)
            TextButton(
              onPressed: () => provider.markAllAsRead(),
              child: const Text('Mark all read'),
            ),
        ],
      ),
      body: provider.isLoading && notifications.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : notifications.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.notifications_none,
                          size: 64, color: theme.colorScheme.outline),
                      const SizedBox(height: 16),
                      const Text('No notifications yet'),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: () => provider.fetchNotifications(),
                  child: ListView.builder(
                    itemCount: notifications.length,
                    itemBuilder: (context, index) {
                      final notif = notifications[index];
                      final typeColor = _colorForType(notif.notificationType, theme);

                      return Dismissible(
                        key: Key(notif.id),
                        direction: DismissDirection.endToStart,
                        background: Container(
                          alignment: Alignment.centerRight,
                          padding: const EdgeInsets.only(right: 20),
                          color: theme.colorScheme.error,
                          child: const Icon(Icons.delete,
                              color: Colors.white),
                        ),
                        onDismissed: (_) {
                          // Optionally handle delete
                        },
                        child: Container(
                          color: notif.isRead
                              ? null
                              : theme.colorScheme.primary
                                  .withOpacity(0.05),
                          child: ListTile(
                            leading: CircleAvatar(
                              backgroundColor:
                                  typeColor.withOpacity(0.15),
                              child: Icon(
                                _iconForType(notif.notificationType),
                                color: typeColor,
                                size: 20,
                              ),
                            ),
                            title: Text(
                              notif.title,
                              style: TextStyle(
                                fontWeight: notif.isRead
                                    ? FontWeight.normal
                                    : FontWeight.bold,
                              ),
                            ),
                            subtitle: Column(
                              crossAxisAlignment:
                                  CrossAxisAlignment.start,
                              children: [
                                if (notif.body.isNotEmpty)
                                  Text(
                                    notif.body,
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                const SizedBox(height: 2),
                                Text(
                                  timeago.format(notif.createdAt),
                                  style: theme.textTheme.bodySmall
                                      ?.copyWith(
                                    color: theme.colorScheme.outline,
                                  ),
                                ),
                              ],
                            ),
                            trailing: !notif.isRead
                                ? Container(
                                    width: 8,
                                    height: 8,
                                    decoration: BoxDecoration(
                                      color: theme.colorScheme.primary,
                                      shape: BoxShape.circle,
                                    ),
                                  )
                                : null,
                            onTap: () => _onTap(notif),
                          ),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}
