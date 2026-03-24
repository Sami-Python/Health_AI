// File generated manually based on frontend configuration.
// ignore_for_file: type=lint
import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;

/// Default [FirebaseOptions] for use with your Firebase apps.
///
/// Example:
/// ```dart
/// import 'firebase_options.dart';
/// // ...
/// await Firebase.initializeApp(
///   options: DefaultFirebaseOptions.currentPlatform,
/// );
/// ```
class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    if (kIsWeb) {
      return web;
    }
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return android;
      case TargetPlatform.iOS:
        return ios;
      case TargetPlatform.macOS:
        throw UnsupportedError(
          'DefaultFirebaseOptions have not been configured for macos - '
          'you can reconfigure this by running the FlutterFire CLI again.',
        );
      case TargetPlatform.windows:
        throw UnsupportedError(
          'DefaultFirebaseOptions have not been configured for windows - '
          'you can reconfigure this by running the FlutterFire CLI again.',
        );
      case TargetPlatform.linux:
        throw UnsupportedError(
          'DefaultFirebaseOptions have not been configured for linux - '
          'you can reconfigure this by running the FlutterFire CLI again.',
        );
      default:
        throw UnsupportedError(
          'DefaultFirebaseOptions are not supported for this platform.',
        );
    }
  }

  static const FirebaseOptions web = FirebaseOptions(
    apiKey: 'AIzaSyDr5wFcRjyPc5MH7_9HlttFQyBOVrNakcc',
    appId: '1:561128557040:web:cc332becd9f322b410b535',
    messagingSenderId: '561128557040',
    projectId: 'personal-ai-coach-92c39',
    authDomain: 'personal-ai-coach-92c39.firebaseapp.com',
    storageBucket: 'personal-ai-coach-92c39.firebasestorage.app',
  );

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'AIzaSyBGzxgQ5k4Qzxjz8P2mRAjnaTMKyQSgacU',
    appId: '1:561128557040:android:d71ae8c6abb3491c10b535',
    messagingSenderId: '561128557040',
    projectId: 'personal-ai-coach-92c39',
    storageBucket: 'personal-ai-coach-92c39.firebasestorage.app',
  );

  static const FirebaseOptions ios = FirebaseOptions(
    apiKey: 'AIzaSyDr5wFcRjyPc5MH7_9HlttFQyBOVrNakcc',
    appId: '1:561128557040:ios:e62a8cc0195c72ca10b535',
    messagingSenderId: '561128557040',
    projectId: 'personal-ai-coach-92c39',
    storageBucket: 'personal-ai-coach-92c39.firebasestorage.app',
    iosClientId: '561128557040-rjiiks5h0ka5vp098dr03erdq3tj95fl.apps.googleusercontent.com',
    iosBundleId: 'com.personalaicoach.mobile',
  );
}
