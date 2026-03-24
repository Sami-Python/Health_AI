import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:mobile/core/services/auth_service.dart';
import 'package:mobile/core/theme/app_theme.dart';
import 'package:mobile/core/services/notification_service.dart';
import 'package:mobile/features/auth/login_screen.dart';
import 'package:mobile/features/dashboard/dashboard_screen.dart';
import 'firebase_options.dart';

// ignore: depend_on_referenced_packages
import 'package:flutter_native_splash/flutter_native_splash.dart';

void main() async {
  WidgetsFlutterBinding binding = WidgetsFlutterBinding.ensureInitialized();
  
  // Keep the splash screen until we are done with basic initialization
  FlutterNativeSplash.preserve(widgetsBinding: binding);

  try {
    await Firebase.initializeApp(
      options: DefaultFirebaseOptions.currentPlatform,
    );
  } catch (e) {
    debugPrint("Firebase init error: $e");
  }
  
  runApp(const HealthAICoachApp());
  
  // Remove splash screen now that basic UI is ready
  FlutterNativeSplash.remove();

  // Initialize Push Notifications in the background so it doesn't block startup
  // (e.g. if waiting for user permission or backend token sync)
  NotificationService().initialize().catchError((e) {
    debugPrint("Notification init error: $e");
  });
}

class HealthAICoachApp extends StatelessWidget {
  const HealthAICoachApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Health AI Coach',
      theme: AppTheme.darkTheme,
      themeMode: ThemeMode.dark,
      debugShowCheckedModeBanner: false,
      home: StreamBuilder(
        stream: AuthService().authStateChanges,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.active) {
            final user = snapshot.data;
            if (user == null) {
              return const LoginScreen();
            }
            return const DashboardScreen();
          }
           // Show loading screen while connecting
          return const Scaffold(
            body: Center(
              child: CircularProgressIndicator(),
            ),
          );
        },
      ),
    );
  }
}
