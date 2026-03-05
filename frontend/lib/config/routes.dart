import 'package:go_router/go_router.dart';

import '../providers/auth_provider.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/register_screen.dart';
import '../screens/auth/eula_screen.dart';
import '../screens/home/home_screen.dart';
import '../screens/profile/edit_profile_screen.dart';
import '../screens/profile/public_profile_screen.dart';
import '../screens/status/create_status_screen.dart';
import '../screens/status/status_list_screen.dart';
import '../screens/chat/chat_rooms_screen.dart';
import '../screens/chat/chat_screen.dart';
import '../screens/chat/connection_requests_screen.dart';
import '../screens/notifications/notifications_screen.dart';
import '../screens/matching/matches_screen.dart';
import '../screens/settings/settings_screen.dart';
import '../screens/home/main_shell.dart';

class AppRouter {
  AppRouter._();

  static GoRouter router(AuthProvider authProvider) {
    return GoRouter(
      refreshListenable: authProvider,
      initialLocation: '/home',
      redirect: (context, state) {
        final isLoggedIn = authProvider.isAuthenticated;
        final isAuthRoute = state.matchedLocation == '/login' ||
            state.matchedLocation == '/register' ||
            state.matchedLocation == '/eula';

        if (!isLoggedIn && !isAuthRoute) return '/login';
        if (isLoggedIn && isAuthRoute) return '/home';
        return null;
      },
      routes: [
        // Auth routes (no shell)
        GoRoute(
          path: '/login',
          name: 'login',
          builder: (context, state) => const LoginScreen(),
        ),
        GoRoute(
          path: '/register',
          name: 'register',
          builder: (context, state) => const RegisterScreen(),
        ),
        GoRoute(
          path: '/eula',
          name: 'eula',
          builder: (context, state) => const EulaScreen(),
        ),

        // Main app shell with bottom navigation
        ShellRoute(
          builder: (context, state, child) => MainShell(child: child),
          routes: [
            GoRoute(
              path: '/home',
              name: 'home',
              builder: (context, state) => const HomeScreen(),
            ),
            GoRoute(
              path: '/chat',
              name: 'chat-rooms',
              builder: (context, state) => const ChatRoomsScreen(),
              routes: [
                GoRoute(
                  path: ':roomId',
                  name: 'chat',
                  builder: (context, state) => ChatScreen(
                    roomId: state.pathParameters['roomId']!,
                  ),
                ),
              ],
            ),
            GoRoute(
              path: '/matches',
              name: 'matches',
              builder: (context, state) => const MatchesScreen(),
            ),
            GoRoute(
              path: '/notifications',
              name: 'notifications',
              builder: (context, state) => const NotificationsScreen(),
            ),
            GoRoute(
              path: '/settings',
              name: 'settings',
              builder: (context, state) => const SettingsScreen(),
            ),
          ],
        ),

        // Full-screen routes (outside shell)
        GoRoute(
          path: '/profile/edit',
          name: 'edit-profile',
          builder: (context, state) => const EditProfileScreen(),
        ),
        GoRoute(
          path: '/profile/:userId',
          name: 'public-profile',
          builder: (context, state) => PublicProfileScreen(
            userId: state.pathParameters['userId']!,
          ),
        ),
        GoRoute(
          path: '/status/create',
          name: 'create-status',
          builder: (context, state) => const CreateStatusScreen(),
        ),
        GoRoute(
          path: '/statuses',
          name: 'status-list',
          builder: (context, state) => const StatusListScreen(),
        ),
        GoRoute(
          path: '/connections',
          name: 'connections',
          builder: (context, state) => const ConnectionRequestsScreen(),
        ),
      ],
    );
  }
}
