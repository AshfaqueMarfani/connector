import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:connector_app/providers/auth_provider.dart';
import 'package:connector_app/screens/auth/register_screen.dart';

void main() {
  Widget buildTestWidget() {
    return ChangeNotifierProvider(
      create: (_) => AuthProvider(),
      child: const MaterialApp(home: RegisterScreen()),
    );
  }

  group('RegisterScreen', () {
    testWidgets('renders all form fields', (tester) async {
      await tester.pumpWidget(buildTestWidget());

      expect(find.text('Create Account'), findsWidgets);
      // 5 fields: full name, email, account type dropdown, password, confirm password
      expect(find.byType(TextFormField), findsNWidgets(4));
      expect(find.byType(DropdownButtonFormField<String>), findsOneWidget);
    });

    testWidgets('renders account type dropdown with 3 options', (tester) async {
      await tester.pumpWidget(buildTestWidget());

      // Open dropdown
      await tester.tap(find.byType(DropdownButtonFormField<String>));
      await tester.pumpAndSettle();

      expect(find.text('Individual'), findsWidgets);
      expect(find.text('Business'), findsWidgets);
      expect(find.text('NGO / Non-Profit'), findsWidgets);
    });

    testWidgets('has EULA checkbox', (tester) async {
      await tester.pumpWidget(buildTestWidget());

      expect(find.byType(CheckboxListTile), findsOneWidget);
      expect(find.textContaining('Terms of Service'), findsOneWidget);
    });

    testWidgets('shows validation errors on empty submit', (tester) async {
      await tester.pumpWidget(buildTestWidget());

      // Scroll to the button
      await tester.scrollUntilVisible(
        find.widgetWithText(ElevatedButton, 'Create Account'),
        100,
        scrollable: find.byType(Scrollable).first,
      );

      await tester.tap(find.widgetWithText(ElevatedButton, 'Create Account'));
      await tester.pump();

      // At least name and email validation errors
      expect(find.textContaining('required'), findsWidgets);
    });

    testWidgets('shows snackbar when EULA not accepted', (tester) async {
      await tester.pumpWidget(buildTestWidget());

      // Fill in all fields
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Full Name'),
        'Test User',
      );
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Email'),
        'test@example.com',
      );

      // Scroll down
      await tester.scrollUntilVisible(
        find.widgetWithText(TextFormField, 'Password'),
        100,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Password'),
        'StrongPass123!',
      );

      await tester.scrollUntilVisible(
        find.widgetWithText(TextFormField, 'Confirm Password'),
        100,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Confirm Password'),
        'StrongPass123!',
      );

      // Scroll to button and tap without checking EULA
      await tester.scrollUntilVisible(
        find.widgetWithText(ElevatedButton, 'Create Account'),
        100,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.tap(find.widgetWithText(ElevatedButton, 'Create Account'));
      await tester.pump();

      expect(find.text('Please accept the Terms of Service'), findsOneWidget);
    });

    testWidgets('has sign in link', (tester) async {
      await tester.pumpWidget(buildTestWidget());

      await tester.scrollUntilVisible(
        find.text('Sign In'),
        100,
        scrollable: find.byType(Scrollable).first,
      );

      expect(find.text('Already have an account? '), findsOneWidget);
      expect(find.text('Sign In'), findsOneWidget);
    });
  });
}
