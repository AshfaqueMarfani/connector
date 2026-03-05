import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'config/routes.dart';
import 'config/theme.dart';
import 'providers/auth_provider.dart';

class ConnectorApp extends StatefulWidget {
  const ConnectorApp({super.key});

  @override
  State<ConnectorApp> createState() => _ConnectorAppState();
}

class _ConnectorAppState extends State<ConnectorApp> {
  @override
  void initState() {
    super.initState();
    // Try to restore auth session on startup
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AuthProvider>().tryAutoLogin();
    });
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();

    return MaterialApp.router(
      title: 'Connector',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
      routerConfig: AppRouter.router(authProvider),
    );
  }
}
