import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:connector_app/screens/auth/eula_screen.dart';

void main() {
  group('EulaScreen', () {
    testWidgets('renders title and all sections', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(home: EulaScreen()),
      );

      // Title
      expect(find.text('Terms of Service'), findsOneWidget);
      expect(find.text('End User License Agreement'), findsOneWidget);

      // Key sections exist
      expect(find.text('1. Acceptance of Terms'), findsOneWidget);
      expect(find.text('2. User-Generated Content'), findsOneWidget);
      expect(find.text('3. Reporting & Moderation'), findsOneWidget);
      expect(find.text('4. Location Data & Privacy'), findsOneWidget);
      expect(find.text('5. Account Security'), findsOneWidget);
      expect(find.text('6. Prohibited Conduct'), findsOneWidget);
    });

    testWidgets('is scrollable to see all content', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(home: EulaScreen()),
      );

      // Scroll down to find later sections
      await tester.scrollUntilVisible(
        find.text('12. Contact'),
        200,
        scrollable: find.byType(Scrollable).first,
      );

      expect(find.text('12. Contact'), findsOneWidget);
    });

    testWidgets('has back button in app bar', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(home: EulaScreen()),
      );

      expect(find.byIcon(Icons.arrow_back), findsOneWidget);
    });
  });
}
