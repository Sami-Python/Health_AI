import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/auth/login_screen.dart';
import 'package:mobile/core/theme/app_theme.dart';

void main() {
  testWidgets('LoginScreen renders correctly', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const MaterialApp(
      home: LoginScreen(),
    ));

    // Verify that our title is present.
    expect(find.text('Personal AI Coach'), findsOneWidget);
    expect(find.text('Your AI-powered recovery assistant'), findsOneWidget);

    // Verify input fields
    expect(find.byType(TextFormField), findsNWidgets(2)); // Email and Password
    expect(find.text('Email'), findsOneWidget);
    expect(find.text('Password'), findsOneWidget);

    // Verify buttons
    expect(find.text('Sign In'), findsOneWidget);
    expect(find.text('Sign in with Google'), findsOneWidget);
  });
}
