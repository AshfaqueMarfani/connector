import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../config/theme.dart';
import '../../models/profile.dart';
import '../../providers/connection_provider.dart';
import '../../providers/moderation_provider.dart';
import '../../providers/profile_provider.dart';

class PublicProfileScreen extends StatefulWidget {
  final String userId;
  const PublicProfileScreen({super.key, required this.userId});

  @override
  State<PublicProfileScreen> createState() => _PublicProfileScreenState();
}

class _PublicProfileScreenState extends State<PublicProfileScreen> {
  Profile? _profile;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final profileProvider = context.read<ProfileProvider>();
      await profileProvider.fetchPublicProfile(widget.userId);
      if (mounted) {
        setState(() {
          _profile = profileProvider.viewedProfile;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _loading = false;
        });
      }
    }
  }

  Future<void> _sendConnectionRequest() async {
    final provider = context.read<ConnectionProvider>();
    final success = await provider.sendRequest(widget.userId);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(success
            ? 'Connection request sent!'
            : provider.error ?? 'Failed to send request'),
        backgroundColor: success ? AppTheme.successColor : AppTheme.errorColor,
      ));
    }
  }

  void _showBlockDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Block User'),
        content: const Text(
            'This user will no longer be able to see you or send you requests. Continue?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: AppTheme.errorColor,
            ),
            onPressed: () async {
              Navigator.pop(ctx);
              final mod = context.read<ModerationProvider>();
              await mod.blockUser(widget.userId);
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                  content: Text('User blocked'),
                ));
              }
            },
            child: const Text('Block'),
          ),
        ],
      ),
    );
  }

  void _showReportDialog() {
    final reasons = [
      'spam',
      'harassment',
      'inappropriate_content',
      'fake_profile',
      'scam',
      'other',
    ];
    String? selectedReason;
    final descController = TextEditingController();

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: const Text('Report User'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<String>(
                value: selectedReason,
                decoration: const InputDecoration(labelText: 'Reason'),
                items: reasons
                    .map((r) => DropdownMenuItem(
                          value: r,
                          child: Text(r.replaceAll('_', ' ')),
                        ))
                    .toList(),
                onChanged: (v) =>
                    setDialogState(() => selectedReason = v),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: descController,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Details (optional)',
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: selectedReason == null
                  ? null
                  : () async {
                      Navigator.pop(ctx);
                      final mod = context.read<ModerationProvider>();
                      await mod.reportContent(
                        reportedUserId: widget.userId,
                        contentType: 'profile',
                        category: selectedReason!,
                        description: descController.text.trim(),
                      );
                      if (mounted) {
                        ScaffoldMessenger.of(context)
                            .showSnackBar(const SnackBar(
                          content: Text('Report submitted'),
                        ));
                      }
                    },
              child: const Text('Submit'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_profile?.effectiveName ?? 'Profile'),
        actions: [
          PopupMenuButton<String>(
            onSelected: (v) {
              if (v == 'block') _showBlockDialog();
              if (v == 'report') _showReportDialog();
            },
            itemBuilder: (_) => [
              const PopupMenuItem(value: 'block', child: Text('Block')),
              const PopupMenuItem(value: 'report', child: Text('Report')),
            ],
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(_error!,
                          style: TextStyle(color: AppTheme.errorColor)),
                      const SizedBox(height: 8),
                      OutlinedButton(
                          onPressed: _load, child: const Text('Retry')),
                    ],
                  ),
                )
              : _buildProfileContent(),
    );
  }

  Widget _buildProfileContent() {
    final p = _profile!;
    final theme = Theme.of(context);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Avatar + Name
          Center(
            child: Column(
              children: [
                CircleAvatar(
                  radius: 48,
                  backgroundImage:
                      p.avatarUrl != null ? NetworkImage(p.avatarUrl!) : null,
                  child: p.avatarUrl == null
                      ? Text(
                          p.effectiveName.isNotEmpty
                              ? p.effectiveName[0].toUpperCase()
                              : '?',
                          style: const TextStyle(fontSize: 28),
                        )
                      : null,
                ),
                const SizedBox(height: 12),
                Text(
                  p.effectiveName,
                  style: theme.textTheme.headlineSmall,
                ),
                const SizedBox(height: 4),
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 10, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppTheme.accountTypeColor(p.user.accountType)
                        .withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    p.user.accountType.toUpperCase(),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.accountTypeColor(p.user.accountType),
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Bio
          if (p.bio.isNotEmpty) ...[
            Text('About',
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(p.bio),
            const SizedBox(height: 20),
          ],

          // Skills
          if (p.skills.isNotEmpty) ...[
            Text('Skills',
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: p.skills
                  .map((s) => Chip(
                        label: Text(s),
                        materialTapTargetSize:
                            MaterialTapTargetSize.shrinkWrap,
                      ))
                  .toList(),
            ),
            const SizedBox(height: 20),
          ],

          // Interests
          if (p.interests.isNotEmpty) ...[
            Text('Interests',
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: p.interests
                  .map((i) => Chip(
                        label: Text(i),
                        materialTapTargetSize:
                            MaterialTapTargetSize.shrinkWrap,
                      ))
                  .toList(),
            ),
            const SizedBox(height: 20),
          ],

          // AI Tags
          if (p.tags.isNotEmpty) ...[
            Text('AI Tags',
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: p.tags
                  .map((t) => Chip(
                        avatar: const Icon(Icons.auto_awesome,
                            size: 16),
                        label: Text(t),
                        materialTapTargetSize:
                            MaterialTapTargetSize.shrinkWrap,
                      ))
                  .toList(),
            ),
            const SizedBox(height: 24),
          ],

          // Connect button
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              icon: const Icon(Icons.person_add_alt_1),
              label: const Text('Send Connection Request'),
              onPressed: _sendConnectionRequest,
            ),
          ),
        ],
      ),
    );
  }
}
