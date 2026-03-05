import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:timeago/timeago.dart' as timeago;

import '../../config/theme.dart';
import '../../models/connection_request.dart';
import '../../providers/connection_provider.dart';

class ConnectionRequestsScreen extends StatefulWidget {
  const ConnectionRequestsScreen({super.key});

  @override
  State<ConnectionRequestsScreen> createState() =>
      _ConnectionRequestsScreenState();
}

class _ConnectionRequestsScreenState extends State<ConnectionRequestsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ConnectionProvider>().fetchRequests();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ConnectionProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Connection Requests'),
        bottom: TabBar(
          controller: _tabController,
          tabs: [
            Tab(
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('Received'),
                  if (provider.receivedPending.isNotEmpty) ...[
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 6, vertical: 1),
                      decoration: BoxDecoration(
                        color: Theme.of(context).colorScheme.primary,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        '${provider.receivedPending.length}',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const Tab(text: 'Sent'),
          ],
        ),
      ),
      body: provider.isLoading && provider.requests.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                _RequestList(
                  requests: provider.receivedPending,
                  emptyMessage: 'No incoming requests',
                  isReceived: true,
                ),
                _RequestList(
                  requests: provider.sentPending,
                  emptyMessage: 'No sent requests',
                  isReceived: false,
                ),
              ],
            ),
    );
  }
}

class _RequestList extends StatelessWidget {
  final List<ConnectionRequest> requests;
  final String emptyMessage;
  final bool isReceived;

  const _RequestList({
    required this.requests,
    required this.emptyMessage,
    required this.isReceived,
  });

  @override
  Widget build(BuildContext context) {
    if (requests.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.people_outline,
                size: 64, color: Theme.of(context).colorScheme.outline),
            const SizedBox(height: 16),
            Text(emptyMessage),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => context.read<ConnectionProvider>().fetchRequests(),
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(vertical: 8),
        itemCount: requests.length,
        itemBuilder: (context, index) {
          return _RequestCard(
            request: requests[index],
            isReceived: isReceived,
          );
        },
      ),
    );
  }
}

class _RequestCard extends StatelessWidget {
  final ConnectionRequest request;
  final bool isReceived;

  const _RequestCard({
    required this.request,
    required this.isReceived,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final provider = context.read<ConnectionProvider>();
    final user = isReceived ? request.fromUser : request.toUser;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            GestureDetector(
              onTap: () => context.push('/profile/${user.id}'),
              child: CircleAvatar(
                radius: 24,
                child: Text(
                  (user.fullName.isNotEmpty ? user.fullName : user.email)[0].toUpperCase(),
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    user.fullName.isNotEmpty ? user.fullName : user.email,
                    style: theme.textTheme.titleSmall,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    timeago.format(request.createdAt),
                    style: theme.textTheme.bodySmall
                        ?.copyWith(color: theme.colorScheme.outline),
                  ),
                ],
              ),
            ),
            if (isReceived) ...[
              IconButton(
                icon: const Icon(Icons.close),
                color: AppTheme.errorColor,
                tooltip: 'Decline',
                onPressed: () async {
                  await provider.declineRequest(request.id);
                },
              ),
              const SizedBox(width: 4),
              FilledButton.icon(
                icon: const Icon(Icons.check, size: 18),
                label: const Text('Accept'),
                style: FilledButton.styleFrom(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12),
                  visualDensity: VisualDensity.compact,
                ),
                onPressed: () async {
                  final chatRoomId =
                      await provider.acceptRequest(request.id);
                  if (chatRoomId != null && context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Connected! Opening chat...'),
                        backgroundColor: AppTheme.successColor,
                      ),
                    );
                    context.push('/chat/$chatRoomId');
                  }
                },
              ),
            ] else ...[
              OutlinedButton(
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppTheme.errorColor,
                  visualDensity: VisualDensity.compact,
                ),
                onPressed: () async {
                  await provider.cancelRequest(request.id);
                },
                child: const Text('Cancel'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
