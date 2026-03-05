import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../config/theme.dart';
import '../../core/utils/validators.dart';
import '../../providers/profile_provider.dart';

class EditProfileScreen extends StatefulWidget {
  const EditProfileScreen({super.key});

  @override
  State<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends State<EditProfileScreen> {
  final _formKey = GlobalKey<FormState>();
  final _displayNameController = TextEditingController();
  final _bioController = TextEditingController();
  final _skillController = TextEditingController();
  final _interestController = TextEditingController();
  List<String> _skills = [];
  List<String> _interests = [];
  bool _isPublic = false;
  bool _liveTracking = false;
  bool _initialized = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_initialized) {
      final profile = context.read<ProfileProvider>().myProfile;
      if (profile != null) {
        _displayNameController.text = profile.displayName;
        _bioController.text = profile.bio;
        _skills = List.from(profile.skills);
        _interests = List.from(profile.interests);
        _isPublic = profile.isPublic;
        _liveTracking = profile.liveTrackingEnabled;
      }
      _initialized = true;
    }
  }

  @override
  void dispose() {
    _displayNameController.dispose();
    _bioController.dispose();
    _skillController.dispose();
    _interestController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;

    final provider = context.read<ProfileProvider>();
    final success = await provider.updateProfile(
      displayName: _displayNameController.text.trim(),
      bio: _bioController.text.trim(),
      skills: _skills,
      interests: _interests,
      isPublic: _isPublic,
      liveTrackingEnabled: _liveTracking,
    );

    if (success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Profile updated'),
          backgroundColor: AppTheme.successColor,
        ),
      );
      context.pop();
    }
  }

  void _addSkill() {
    final text = _skillController.text.trim().toLowerCase();
    if (text.isNotEmpty && !_skills.contains(text) && _skills.length < 20) {
      setState(() => _skills.add(text));
      _skillController.clear();
    }
  }

  void _addInterest() {
    final text = _interestController.text.trim().toLowerCase();
    if (text.isNotEmpty &&
        !_interests.contains(text) &&
        _interests.length < 20) {
      setState(() => _interests.add(text));
      _interestController.clear();
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ProfileProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Edit Profile'),
        actions: [
          TextButton(
            onPressed: provider.isLoading ? null : _save,
            child: provider.isLoading
                ? const SizedBox(
                    height: 16,
                    width: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Text('Save'),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Avatar
              Center(
                child: GestureDetector(
                  onTap: () {
                    // TODO: Image picker
                  },
                  child: CircleAvatar(
                    radius: 48,
                    backgroundImage: provider.myProfile?.avatarUrl != null
                        ? NetworkImage(provider.myProfile!.avatarUrl!)
                        : null,
                    child: provider.myProfile?.avatarUrl == null
                        ? const Icon(Icons.camera_alt, size: 32)
                        : null,
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Display Name
              TextFormField(
                controller: _displayNameController,
                decoration: const InputDecoration(
                  labelText: 'Display Name',
                  prefixIcon: Icon(Icons.person_outlined),
                ),
              ),
              const SizedBox(height: 16),

              // Bio
              TextFormField(
                controller: _bioController,
                maxLines: 3,
                maxLength: 500,
                validator: Validators.bio,
                decoration: const InputDecoration(
                  labelText: 'Bio',
                  alignLabelWithHint: true,
                  prefixIcon: Icon(Icons.info_outlined),
                ),
              ),
              const SizedBox(height: 16),

              // Skills
              const Text('Skills',
                  style: TextStyle(fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _skillController,
                      decoration: const InputDecoration(
                        hintText: 'Add a skill...',
                        isDense: true,
                      ),
                      onSubmitted: (_) => _addSkill(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    icon: const Icon(Icons.add_circle),
                    color: AppTheme.primaryColor,
                    onPressed: _addSkill,
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: _skills
                    .map((s) => Chip(
                          label: Text(s),
                          deleteIcon:
                              const Icon(Icons.close, size: 16),
                          onDeleted: () =>
                              setState(() => _skills.remove(s)),
                        ))
                    .toList(),
              ),
              const SizedBox(height: 16),

              // Interests
              const Text('Interests',
                  style: TextStyle(fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _interestController,
                      decoration: const InputDecoration(
                        hintText: 'Add an interest...',
                        isDense: true,
                      ),
                      onSubmitted: (_) => _addInterest(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    icon: const Icon(Icons.add_circle),
                    color: AppTheme.primaryColor,
                    onPressed: _addInterest,
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: _interests
                    .map((i) => Chip(
                          label: Text(i),
                          deleteIcon:
                              const Icon(Icons.close, size: 16),
                          onDeleted: () =>
                              setState(() => _interests.remove(i)),
                        ))
                    .toList(),
              ),
              const SizedBox(height: 24),

              // AI tag generation
              OutlinedButton.icon(
                icon: const Icon(Icons.auto_awesome),
                label: const Text('Generate AI Tags'),
                onPressed: () async {
                  final success =
                      await context.read<ProfileProvider>().generateAiTags();
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                      content: Text(success
                          ? 'AI tag generation queued. Refresh shortly.'
                          : 'Failed to queue tag generation.'),
                    ));
                  }
                },
              ),
              const SizedBox(height: 24),

              // Privacy toggles
              SwitchListTile(
                title: const Text('Public Profile'),
                subtitle: const Text(
                    'Show exact location on map (businesses & NGOs)'),
                value: _isPublic,
                onChanged: (v) => setState(() => _isPublic = v),
              ),
              SwitchListTile(
                title: const Text('Live Tracking'),
                subtitle: const Text(
                    'Allow background location updates'),
                value: _liveTracking,
                onChanged: (v) => setState(() => _liveTracking = v),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
