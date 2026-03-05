import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'app.dart';
import 'core/storage/secure_storage.dart';
import 'providers/auth_provider.dart';
import 'providers/profile_provider.dart';
import 'providers/location_provider.dart';
import 'providers/status_provider.dart';
import 'providers/chat_provider.dart';
import 'providers/connection_provider.dart';
import 'providers/notification_provider.dart';
import 'providers/matching_provider.dart';
import 'providers/moderation_provider.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await SecureStorage.init();

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProxyProvider<AuthProvider, ProfileProvider>(
          create: (_) => ProfileProvider(),
          update: (_, auth, profile) => profile!..updateAuth(auth),
        ),
        ChangeNotifierProxyProvider<AuthProvider, LocationProvider>(
          create: (_) => LocationProvider(),
          update: (_, auth, loc) => loc!..updateAuth(auth),
        ),
        ChangeNotifierProxyProvider<AuthProvider, StatusProvider>(
          create: (_) => StatusProvider(),
          update: (_, auth, status) => status!..updateAuth(auth),
        ),
        ChangeNotifierProxyProvider<AuthProvider, ChatProvider>(
          create: (_) => ChatProvider(),
          update: (_, auth, chat) => chat!..updateAuth(auth),
        ),
        ChangeNotifierProxyProvider<AuthProvider, ConnectionProvider>(
          create: (_) => ConnectionProvider(),
          update: (_, auth, conn) => conn!..updateAuth(auth),
        ),
        ChangeNotifierProxyProvider<AuthProvider, NotificationProvider>(
          create: (_) => NotificationProvider(),
          update: (_, auth, notif) => notif!..updateAuth(auth),
        ),
        ChangeNotifierProxyProvider<AuthProvider, MatchingProvider>(
          create: (_) => MatchingProvider(),
          update: (_, auth, match) => match!..updateAuth(auth),
        ),
        ChangeNotifierProxyProvider<AuthProvider, ModerationProvider>(
          create: (_) => ModerationProvider(),
          update: (_, auth, mod) => mod!..updateAuth(auth),
        ),
      ],
      child: const ConnectorApp(),
    ),
  );
}
