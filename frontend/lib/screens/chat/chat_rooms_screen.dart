import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:timeago/timeago.dart' as timeago;

import '../../models/chat_room.dart';
import '../../providers/auth_provider.dart';
import '../../providers/chat_provider.dart';

class ChatRoomsScreen extends StatefulWidget {
  const ChatRoomsScreen({super.key});

  @override
  State<ChatRoomsScreen> createState() => _ChatRoomsScreenState();
}

class _ChatRoomsScreenState extends State<ChatRoomsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ChatProvider>().fetchRooms();
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ChatProvider>();
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Messages'),
        actions: [
          IconButton(
            icon: const Icon(Icons.people_alt_outlined),
            tooltip: 'Connection Requests',
            onPressed: () => context.push('/connections'),
          ),
        ],
      ),
      body: provider.isLoading && provider.rooms.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : provider.rooms.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.chat_bubble_outline,
                          size: 64, color: theme.colorScheme.outline),
                      const SizedBox(height: 16),
                      const Text('No conversations yet'),
                      const SizedBox(height: 8),
                      const Text(
                        'Connect with nearby people to start chatting',
                        style: TextStyle(fontSize: 13),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: () => provider.fetchRooms(),
                  child: ListView.builder(
                    itemCount: provider.rooms.length,
                    itemBuilder: (context, index) {
                      final room = provider.rooms[index];
                      return _ChatRoomTile(room: room);
                    },
                  ),
                ),
    );
  }
}

class _ChatRoomTile extends StatelessWidget {
  final ChatRoom room;
  const _ChatRoomTile({required this.room});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final currentUserId = context.read<AuthProvider>().userId;
    final other = room.otherParticipant(currentUserId);
    final hasUnread = room.unreadCount > 0;

    return ListTile(
      leading: CircleAvatar(
        child: Text(
          (other?.fullName ?? '?')[0].toUpperCase(),
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      title: Row(
        children: [
          Expanded(
            child: Text(
              other?.fullName ?? 'User',
              style: TextStyle(
                fontWeight: hasUnread ? FontWeight.bold : FontWeight.normal,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (room.lastMessage != null)
            Text(
              timeago.format(room.lastMessage!.createdAt),
              style: theme.textTheme.bodySmall?.copyWith(
                color: hasUnread
                    ? theme.colorScheme.primary
                    : theme.colorScheme.outline,
                fontWeight: hasUnread ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
        ],
      ),
      subtitle: Row(
        children: [
          if (room.lastMessage != null)
            Expanded(
              child: Text(
                room.lastMessage!.messageType == 'location'
                    ? '📍 Shared location'
                    : room.lastMessage!.content,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontWeight: hasUnread ? FontWeight.w500 : FontWeight.normal,
                ),
              ),
            )
          else
            Expanded(
              child: Text(
                'No messages yet',
                style: TextStyle(color: theme.colorScheme.outline),
              ),
            ),
          if (hasUnread)
            Container(
              margin: const EdgeInsets.only(left: 6),
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: theme.colorScheme.primary,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                '${room.unreadCount}',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
        ],
      ),
      onTap: () => context.push('/chat/${room.id}'),
    );
  }
}
