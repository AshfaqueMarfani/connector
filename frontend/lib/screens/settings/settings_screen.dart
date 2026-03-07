import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../config/theme.dart';
import '../../providers/auth_provider.dart';
import '../../providers/location_provider.dart';
import '../../providers/moderation_provider.dart';
import '../../providers/profile_provider.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final auth = context.watch<AuthProvider>();
    final profile = context.watch<ProfileProvider>();
    final location = context.watch<LocationProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        children: [
          // Profile header
          Container(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 30,
                  backgroundImage: profile.myProfile?.avatarUrl != null
                      ? NetworkImage(profile.myProfile!.avatarUrl!)
                      : null,
                  child: profile.myProfile?.avatarUrl == null
                      ? Text(
                          (auth.user?.fullName ?? '?')[0].toUpperCase(),
                          style: const TextStyle(fontSize: 20),
                        )
                      : null,
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        profile.myProfile?.effectiveName ??
                            auth.user?.fullName ??
                            'User',
                        style: theme.textTheme.titleMedium,
                      ),
                      const SizedBox(height: 2),
                      Text(
                        auth.user?.email ?? '',
                        style: theme.textTheme.bodySmall
                            ?.copyWith(color: theme.colorScheme.outline),
                      ),
                      if (auth.user?.accountType != null) ...[
                        const SizedBox(height: 4),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppTheme.accountTypeColor(
                                    auth.user!.accountType)
                                .withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            auth.user!.accountType.toUpperCase(),
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.w600,
                              color: AppTheme.accountTypeColor(
                                  auth.user!.accountType),
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.edit),
                  onPressed: () => context.push('/profile/edit'),
                ),
              ],
            ),
          ),
          const Divider(height: 1),

          // Profile section
          const _SectionHeader(title: 'Profile'),
          ListTile(
            leading: const Icon(Icons.person_outline),
            title: const Text('Edit Profile'),
            subtitle: const Text('Name, bio, skills, interests'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push('/profile/edit'),
          ),
          ListTile(
            leading: const Icon(Icons.assignment_outlined),
            title: const Text('My Statuses'),
            subtitle: const Text('View and manage your needs & offers'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push('/statuses'),
          ),

          const Divider(height: 1),

          // Location & Privacy
          const _SectionHeader(title: 'Location & Privacy'),
          SwitchListTile(
            secondary: const Icon(Icons.location_on_outlined),
            title: const Text('Live Tracking'),
            subtitle: const Text('Share real-time location updates'),
            value: profile.myProfile?.liveTrackingEnabled ?? false,
            onChanged: (v) {
              profile.updateProfile(liveTrackingEnabled: v);
            },
          ),
          SwitchListTile(
            secondary: const Icon(Icons.visibility_outlined),
            title: const Text('Public Profile'),
            subtitle: const Text('Show exact location on map'),
            value: profile.myProfile?.isPublic ?? false,
            onChanged: (v) {
              profile.updateProfile(isPublic: v);
            },
          ),
          ListTile(
            leading: const Icon(Icons.my_location),
            title: const Text('Update Location'),
            subtitle: Text(location.myLocation != null
                ? 'Last: ${location.myLocation!.latitude.toStringAsFixed(4)}, ${location.myLocation!.longitude.toStringAsFixed(4)}'
                : 'Location not set'),
            trailing: location.isLoading
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.refresh),
            onTap: () => location.updateLocation(),
          ),

          const Divider(height: 1),

          // Moderation
          const _SectionHeader(title: 'Safety'),
          ListTile(
            leading: const Icon(Icons.block),
            title: const Text('Blocked Users'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _showBlockedUsers(context),
          ),

          const Divider(height: 1),

          // Account
          const _SectionHeader(title: 'Account'),
          ListTile(
            leading: const Icon(Icons.info_outline),
            title: const Text('About Connector'),
            onTap: () {
              showAboutDialog(
                context: context,
                applicationName: 'Connector',
                applicationVersion: '1.0.0',
                applicationLegalese:
                    '© 2024 Connector. Connecting communities.',
              );
            },
          ),
          ListTile(
            leading: const Icon(Icons.logout, color: AppTheme.errorColor),
            title: const Text('Log Out',
                style: TextStyle(color: AppTheme.errorColor)),
            onTap: () => _confirmLogout(context),
          ),

          const SizedBox(height: 40),
        ],
      ),
    );
  }

  void _confirmLogout(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Log Out'),
        content: const Text('Are you sure you want to log out?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style:
                FilledButton.styleFrom(backgroundColor: AppTheme.errorColor),
            onPressed: () {
              Navigator.pop(ctx);
              context.read<AuthProvider>().logout();
            },
            child: const Text('Log Out'),
          ),
        ],
      ),
    );
  }

  void _showBlockedUsers(BuildContext context) {
    final modProvider = context.read<ModerationProvider>();
    modProvider.fetchBlockedUsers();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.5,
        minChildSize: 0.3,
        maxChildSize: 0.8,
        expand: false,
        builder: (ctx, scrollController) {
          return Consumer<ModerationProvider>(
            builder: (ctx, mod, _) {
              return Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        Text(
                          'Blocked Users',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const Spacer(),
                        IconButton(
                          icon: const Icon(Icons.close),
                          onPressed: () => Navigator.pop(ctx),
                        ),
                      ],
                    ),
                  ),
                  const Divider(height: 1),
                  Expanded(
                    child: mod.isLoading
                        ? const Center(child: CircularProgressIndicator())
                        : mod.blockedUsers.isEmpty
                            ? const Center(
                                child: Text('No blocked users'))
                            : ListView.builder(
                                controller: scrollController,
                                itemCount: mod.blockedUsers.length,
                                itemBuilder: (ctx, index) {
                                  final user = mod.blockedUsers[index];
                                  final name = user['blocked_detail']?['full_name'] as String? ??
                                      user['blocked'] as String? ?? '?';
                                  final blockedId = user['blocked'] as String? ?? '';
                                  return ListTile(
                                    leading: CircleAvatar(
                                      child: Text(
                                        name.isNotEmpty
                                            ? name[0].toUpperCase()
                                            : '?',
                                      ),
                                    ),
                                    title: Text(name),
                                    trailing: OutlinedButton(
                                      onPressed: () async {
                                        await mod
                                            .unblockUser(blockedId);
                                      },
                                      child: const Text('Unblock'),
                                    ),
                                  );
                                },
                              ),
                  ),
                ],
              );
            },
          );
        },
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  const _SectionHeader({required this.title});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 8),
      child: Text(
        title,
        style: Theme.of(context).textTheme.labelLarge?.copyWith(
              color: Theme.of(context).colorScheme.primary,
              fontWeight: FontWeight.bold,
            ),
      ),
    );
  }
}
