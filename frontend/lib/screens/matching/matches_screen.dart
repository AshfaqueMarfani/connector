import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../config/theme.dart';
import '../../models/match_result.dart';
import '../../providers/matching_provider.dart';

class MatchesScreen extends StatefulWidget {
  const MatchesScreen({super.key});

  @override
  State<MatchesScreen> createState() => _MatchesScreenState();
}

class _MatchesScreenState extends State<MatchesScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider = context.read<MatchingProvider>();
      provider.fetchMatches();
      provider.fetchSentMatches();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<MatchingProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Matches'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'For You'),
            Tab(text: 'Sent'),
          ],
        ),
      ),
      body: provider.isLoading &&
              provider.matches.isEmpty &&
              provider.sentMatches.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                _MatchList(
                  matches: provider.matches,
                  emptyMessage: 'No match suggestions yet',
                  emptySubtitle:
                      'Post a need or offer to get AI-powered matches',
                  showDismiss: true,
                ),
                _MatchList(
                  matches: provider.sentMatches,
                  emptyMessage: 'No sent matches',
                  emptySubtitle: 'Your outgoing match notifications',
                  showDismiss: false,
                ),
              ],
            ),
    );
  }
}

class _MatchList extends StatelessWidget {
  final List<MatchResult> matches;
  final String emptyMessage;
  final String emptySubtitle;
  final bool showDismiss;

  const _MatchList({
    required this.matches,
    required this.emptyMessage,
    required this.emptySubtitle,
    required this.showDismiss,
  });

  @override
  Widget build(BuildContext context) {
    if (matches.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.auto_awesome,
                size: 64, color: Theme.of(context).colorScheme.outline),
            const SizedBox(height: 16),
            Text(emptyMessage),
            const SizedBox(height: 4),
            Text(
              emptySubtitle,
              style: Theme.of(context)
                  .textTheme
                  .bodySmall
                  ?.copyWith(color: Theme.of(context).colorScheme.outline),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () async {
        final provider = context.read<MatchingProvider>();
        await provider.fetchMatches();
        await provider.fetchSentMatches();
      },
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(vertical: 8),
        itemCount: matches.length,
        itemBuilder: (context, index) {
          return _MatchCard(
            match: matches[index],
            showDismiss: showDismiss,
          );
        },
      ),
    );
  }
}

class _MatchCard extends StatelessWidget {
  final MatchResult match;
  final bool showDismiss;

  const _MatchCard({required this.match, required this.showDismiss});

  String get _userName => match.matchedUserDetail?.fullName ?? 'Unknown';
  String get _userId => match.matchedUserDetail?.id ?? '';

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => context.push('/profile/$_userId'),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header: avatar + name + score
              Row(
                children: [
                  CircleAvatar(
                    radius: 22,
                    child: Text(
                      _userName.isNotEmpty
                          ? _userName[0].toUpperCase()
                          : '?',
                      style: const TextStyle(
                          fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _userName,
                          style: theme.textTheme.titleSmall,
                        ),
                        const SizedBox(height: 2),
                        Text(
                          match.distanceFormatted,
                          style: theme.textTheme.bodySmall
                              ?.copyWith(color: theme.colorScheme.outline),
                        ),
                      ],
                    ),
                  ),
                  // Score ring
                  _ScoreIndicator(score: (match.score * 100).round()),
                ],
              ),
              const SizedBox(height: 12),

              // Matching tags
              if (match.matchedTags.isNotEmpty) ...[
                Text(
                  'Matching Tags',
                  style: theme.textTheme.labelSmall
                      ?.copyWith(color: theme.colorScheme.outline),
                ),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 6,
                  runSpacing: 4,
                  children: match.matchedTags
                      .map((tag) => Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: AppTheme.accentColor.withValues(alpha: 0.12),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              tag,
                              style: const TextStyle(
                                fontSize: 12,
                                color: AppTheme.accentColor,
                              ),
                            ),
                          ))
                      .toList(),
                ),
                const SizedBox(height: 12),
              ],

              // Status info
              if (match.statusDetail != null) ...[
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color:
                        theme.colorScheme.surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            match.statusDetail!.statusType == 'need'
                                ? Icons.front_hand
                                : Icons.volunteer_activism,
                            size: 14,
                            color: theme.colorScheme.outline,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            'Their ${match.statusDetail!.statusType}',
                            style: theme.textTheme.labelSmall?.copyWith(
                              color: theme.colorScheme.outline,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        match.statusDetail!.text,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: theme.textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
              ],

              // Actions
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  if (showDismiss)
                    OutlinedButton.icon(
                      icon: const Icon(Icons.close, size: 16),
                      label: const Text('Dismiss'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: theme.colorScheme.outline,
                        visualDensity: VisualDensity.compact,
                      ),
                      onPressed: () async {
                        await context
                            .read<MatchingProvider>()
                            .dismissMatch(match.id);
                      },
                    ),
                  const SizedBox(width: 8),
                  FilledButton.icon(
                    icon: const Icon(Icons.person, size: 16),
                    label: const Text('View Profile'),
                    style: FilledButton.styleFrom(
                      visualDensity: VisualDensity.compact,
                    ),
                    onPressed: () =>
                        context.push('/profile/$_userId'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ScoreIndicator extends StatelessWidget {
  final int score;
  const _ScoreIndicator({required this.score});

  @override
  Widget build(BuildContext context) {
    final color = score >= 70
        ? AppTheme.successColor
        : score >= 40
            ? Colors.orange
            : Colors.grey;

    return SizedBox(
      width: 48,
      height: 48,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CircularProgressIndicator(
            value: score / 100,
            strokeWidth: 4,
            backgroundColor: color.withValues(alpha: 0.15),
            color: color,
          ),
          Text(
            '$score%',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}
