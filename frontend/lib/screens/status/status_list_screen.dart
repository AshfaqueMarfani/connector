import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:timeago/timeago.dart' as timeago;

import '../../config/theme.dart';
import '../../models/status.dart';
import '../../providers/status_provider.dart';

class StatusListScreen extends StatefulWidget {
  const StatusListScreen({super.key});

  @override
  State<StatusListScreen> createState() => _StatusListScreenState();
}

class _StatusListScreenState extends State<StatusListScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<StatusProvider>().fetchMyStatuses();
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<StatusProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Statuses'),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/status/create'),
        icon: const Icon(Icons.add),
        label: const Text('New'),
      ),
      body: provider.isLoading && provider.statuses.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : provider.statuses.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.assignment_outlined,
                          size: 64,
                          color: Theme.of(context).colorScheme.outline),
                      const SizedBox(height: 16),
                      const Text('No statuses yet'),
                      const SizedBox(height: 8),
                      FilledButton.tonalIcon(
                        onPressed: () => context.push('/status/create'),
                        icon: const Icon(Icons.add),
                        label: const Text('Post a status'),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: () => provider.fetchMyStatuses(),
                  child: ListView.builder(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    itemCount: provider.statuses.length,
                    itemBuilder: (context, index) {
                      final status = provider.statuses[index];
                      return _StatusCard(status: status);
                    },
                  ),
                ),
    );
  }
}

class _StatusCard extends StatelessWidget {
  final Status status;
  const _StatusCard({required this.status});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isActive = status.isActive;
    final isNeed = status.isNeed;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header row
            Row(
              children: [
                // Type badge
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: (isNeed ? Colors.orange : Colors.teal)
                        .withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        isNeed
                            ? Icons.front_hand
                            : Icons.volunteer_activism,
                        size: 14,
                        color: isNeed ? Colors.orange : Colors.teal,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        isNeed ? 'Need' : 'Offer',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: isNeed ? Colors.orange : Colors.teal,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),

                // Urgency badge
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppTheme.urgencyColor(status.urgency)
                        .withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    status.urgency.toUpperCase(),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.urgencyColor(status.urgency),
                    ),
                  ),
                ),
                const Spacer(),

                // Active / Inactive chip
                Chip(
                  label: Text(
                    isActive ? 'Active' : 'Inactive',
                    style: TextStyle(
                      fontSize: 11,
                      color: isActive
                          ? AppTheme.successColor
                          : theme.colorScheme.outline,
                    ),
                  ),
                  backgroundColor: isActive
                      ? AppTheme.successColor.withValues(alpha: 0.1)
                      : theme.colorScheme.surfaceContainerHighest,
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  visualDensity: VisualDensity.compact,
                ),
              ],
            ),
            const SizedBox(height: 10),

            // Text
            Text(status.text, style: theme.textTheme.bodyLarge),
            const SizedBox(height: 8),

            // Timestamp + actions
            Row(
              children: [
                Text(
                  timeago.format(status.createdAt),
                  style: theme.textTheme.bodySmall
                      ?.copyWith(color: theme.colorScheme.outline),
                ),
                const Spacer(),
                if (isActive)
                  TextButton.icon(
                    style: TextButton.styleFrom(
                      foregroundColor: AppTheme.errorColor,
                      visualDensity: VisualDensity.compact,
                    ),
                    icon: const Icon(Icons.cancel_outlined, size: 18),
                    label: const Text('Deactivate'),
                    onPressed: () async {
                      final confirm = await showDialog<bool>(
                        context: context,
                        builder: (ctx) => AlertDialog(
                          title: const Text('Deactivate Status'),
                          content: const Text(
                              'This status will no longer be visible to others.'),
                          actions: [
                            TextButton(
                              onPressed: () => Navigator.pop(ctx, false),
                              child: const Text('Cancel'),
                            ),
                            FilledButton(
                              onPressed: () => Navigator.pop(ctx, true),
                              child: const Text('Deactivate'),
                            ),
                          ],
                        ),
                      );
                      if (confirm == true && context.mounted) {
                        await context
                            .read<StatusProvider>()
                            .deactivateStatus(status.id);
                      }
                    },
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
