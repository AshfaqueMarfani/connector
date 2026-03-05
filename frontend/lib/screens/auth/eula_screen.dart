import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// Full EULA / Terms of Service screen – mandatory for App Store UGC compliance.
class EulaScreen extends StatelessWidget {
  const EulaScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
        title: const Text('Terms of Service'),
      ),
      body: const SafeArea(
        child: SingleChildScrollView(
          padding: EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'End User License Agreement',
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 8),
              Text(
                'Last Updated: January 2025',
                style: TextStyle(color: Colors.grey, fontSize: 13),
              ),
              SizedBox(height: 24),

              // Section 1
              _SectionTitle(text: '1. Acceptance of Terms'),
              _SectionBody(
                text:
                    'By creating an account or using the Connector application '
                    '("App"), you agree to be bound by these Terms of Service '
                    'and End User License Agreement ("Agreement"). If you do '
                    'not agree to all terms, you must not use the App.',
              ),

              // Section 2
              _SectionTitle(text: '2. User-Generated Content'),
              _SectionBody(
                text:
                    'The App allows you to post statuses, messages, and profile '
                    'information ("User Content"). You are solely responsible '
                    'for the content you create. By submitting User Content, '
                    'you grant the App a non-exclusive, worldwide license to '
                    'display, distribute, and process your content for the '
                    'purpose of operating the service.\n\n'
                    'You agree NOT to post content that:\n'
                    '• Is illegal, harmful, threatening, abusive, or harassing\n'
                    '• Contains hate speech, discrimination, or promotes violence\n'
                    '• Infringes intellectual property rights of others\n'
                    '• Contains personal information of others without consent\n'
                    '• Is spam, advertising, or commercial solicitation\n'
                    '• Contains malware, viruses, or harmful code',
              ),

              // Section 3
              _SectionTitle(text: '3. Reporting & Moderation'),
              _SectionBody(
                text:
                    'We provide tools for users to report inappropriate content '
                    'and block other users. All reported content is reviewed by '
                    'our moderation team. We reserve the right to remove any '
                    'content and suspend or terminate accounts that violate '
                    'these terms, at our sole discretion and without notice.',
              ),

              // Section 4
              _SectionTitle(text: '4. Location Data & Privacy'),
              _SectionBody(
                text:
                    'The App uses your device location to provide hyperlocal '
                    'services. For private profiles, your exact location is '
                    'never displayed publicly — only an approximate zone is '
                    'shown on the map.\n\n'
                    'Location data is collected only when:\n'
                    '• The App is in the foreground (default)\n'
                    '• You explicitly enable "Live Tracking" mode\n\n'
                    'You can revoke location permissions at any time through '
                    'your device settings. Some features may not function '
                    'without location access.',
              ),

              // Section 5
              _SectionTitle(text: '5. Account Security'),
              _SectionBody(
                text:
                    'You are responsible for maintaining the confidentiality '
                    'of your account credentials. You must immediately notify '
                    'us of any unauthorized use of your account. We are not '
                    'liable for losses arising from unauthorized use of your '
                    'credentials.',
              ),

              // Section 6
              _SectionTitle(text: '6. Prohibited Conduct'),
              _SectionBody(
                text:
                    'You agree not to:\n'
                    '• Impersonate any person or entity\n'
                    '• Use the App for illegal activities\n'
                    '• Attempt to access other users\' accounts\n'
                    '• Interfere with or disrupt the service\n'
                    '• Scrape, crawl, or harvest user data\n'
                    '• Use automated systems to access the service\n'
                    '• Circumvent any security features',
              ),

              // Section 7
              _SectionTitle(text: '7. Service Availability'),
              _SectionBody(
                text:
                    'We strive to maintain continuous service availability but '
                    'do not guarantee uninterrupted access. The service may be '
                    'temporarily unavailable for maintenance, updates, or '
                    'circumstances beyond our control.',
              ),

              // Section 8
              _SectionTitle(text: '8. Termination'),
              _SectionBody(
                text:
                    'We may terminate or suspend your account at any time for '
                    'violation of these terms. You may delete your account at '
                    'any time through the App settings. Upon termination, your '
                    'right to use the App ceases immediately.',
              ),

              // Section 9
              _SectionTitle(text: '9. Disclaimer of Warranties'),
              _SectionBody(
                text:
                    'THE APP IS PROVIDED "AS IS" WITHOUT WARRANTIES OF ANY '
                    'KIND. WE DISCLAIM ALL WARRANTIES, EXPRESS OR IMPLIED, '
                    'INCLUDING MERCHANTABILITY, FITNESS FOR A PARTICULAR '
                    'PURPOSE, AND NON-INFRINGEMENT. WE DO NOT WARRANT THAT '
                    'THE SERVICE WILL BE ERROR-FREE OR UNINTERRUPTED.',
              ),

              // Section 10
              _SectionTitle(text: '10. Limitation of Liability'),
              _SectionBody(
                text:
                    'TO THE MAXIMUM EXTENT PERMITTED BY LAW, WE SHALL NOT BE '
                    'LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, OR '
                    'CONSEQUENTIAL DAMAGES ARISING FROM YOUR USE OF THE APP, '
                    'INCLUDING BUT NOT LIMITED TO DAMAGES FOR LOSS OF PROFITS, '
                    'DATA, OR OTHER INTANGIBLE LOSSES.',
              ),

              // Section 11
              _SectionTitle(text: '11. Changes to Terms'),
              _SectionBody(
                text:
                    'We reserve the right to modify these terms at any time. '
                    'Continued use of the App after changes constitutes '
                    'acceptance of the updated terms. We will notify users of '
                    'material changes through the App.',
              ),

              // Section 12
              _SectionTitle(text: '12. Contact'),
              _SectionBody(
                text:
                    'For questions about these terms, contact us at:\n'
                    'support@otaskflow.com\n\n'
                    'By creating an account, you acknowledge that you have '
                    'read, understood, and agree to be bound by this Agreement.',
              ),

              SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String text;
  const _SectionTitle({required this.text});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 20, bottom: 8),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class _SectionBody extends StatelessWidget {
  final String text;
  const _SectionBody({required this.text});

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: TextStyle(
        fontSize: 14,
        height: 1.6,
        color: Colors.grey[800],
      ),
    );
  }
}
