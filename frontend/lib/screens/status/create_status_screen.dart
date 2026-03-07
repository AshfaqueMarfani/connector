import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../config/theme.dart';
import '../../providers/status_provider.dart';

class CreateStatusScreen extends StatefulWidget {
  const CreateStatusScreen({super.key});

  @override
  State<CreateStatusScreen> createState() => _CreateStatusScreenState();
}

class _CreateStatusScreenState extends State<CreateStatusScreen> {
  final _formKey = GlobalKey<FormState>();
  final _textController = TextEditingController();
  String _statusType = 'need';
  String _urgency = 'medium';

  static const _urgencyOptions = ['low', 'medium', 'high', 'emergency'];

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    final provider = context.read<StatusProvider>();
    final success = await provider.createStatus(
      statusType: _statusType,
      text: _textController.text.trim(),
      urgency: _urgency,
    );

    if (success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Status posted!'),
          backgroundColor: AppTheme.successColor,
        ),
      );
      context.pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<StatusProvider>();
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Post Status')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Error banner
              if (provider.error != null)
                Container(
                  width: double.infinity,
                  margin: const EdgeInsets.only(bottom: 16),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppTheme.errorColor.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(provider.error!,
                      style: const TextStyle(color: AppTheme.errorColor)),
                ),

              // Type selector
              Text('Type', style: theme.textTheme.titleMedium),
              const SizedBox(height: 8),
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(
                    value: 'need',
                    icon: Icon(Icons.front_hand),
                    label: Text('Need'),
                  ),
                  ButtonSegment(
                    value: 'offer',
                    icon: Icon(Icons.volunteer_activism),
                    label: Text('Offer'),
                  ),
                ],
                selected: {_statusType},
                onSelectionChanged: (v) =>
                    setState(() => _statusType = v.first),
              ),
              const SizedBox(height: 24),

              // Text
              TextFormField(
                controller: _textController,
                maxLines: 4,
                maxLength: 500,
                decoration: InputDecoration(
                  labelText: _statusType == 'need'
                      ? 'What do you need?'
                      : 'What are you offering?',
                  alignLabelWithHint: true,
                  prefixIcon: const Icon(Icons.edit_note),
                ),
                validator: (v) {
                  if (v == null || v.trim().isEmpty) {
                    return 'Please describe your $_statusType.';
                  }
                  if (v.trim().length < 5) {
                    return 'Must be at least 5 characters.';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 24),

              // Urgency
              Text('Urgency', style: theme.textTheme.titleMedium),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                children: _urgencyOptions
                    .map((u) => ChoiceChip(
                          label: Text(u[0].toUpperCase() + u.substring(1)),
                          selected: _urgency == u,
                          selectedColor:
                              AppTheme.urgencyColor(u).withValues(alpha: 0.25),
                          onSelected: (_) =>
                              setState(() => _urgency = u),
                        ))
                    .toList(),
              ),
              const SizedBox(height: 32),

              // Submit
              SizedBox(
                width: double.infinity,
                height: 48,
                child: FilledButton(
                  onPressed: provider.isLoading ? null : _submit,
                  child: provider.isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child:
                              CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Post Status'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
