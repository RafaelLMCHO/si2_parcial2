import 'package:go_router/go_router.dart';

import '../../features/auth/presentation/login_screen.dart';
import '../../features/auth/presentation/register_screen.dart';
import '../../features/auth/presentation/verify_email_screen.dart';
import '../../features/profile/presentation/profile_screen.dart';
import '../session/session_controller.dart';

GoRouter createRouter(SessionController session) {
  return GoRouter(
    initialLocation: session.isAuthenticated ? '/profile' : '/login',
    refreshListenable: session,
    redirect: (context, state) {
      final location = state.matchedLocation;
      final isAuthRoute =
          location == '/login' ||
          location == '/register' ||
          location == '/verify-email';

      if (!session.isAuthenticated && !isAuthRoute) {
        return '/login';
      }
      if (session.isAuthenticated && isAuthRoute) {
        return '/profile';
      }
      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => LoginScreen(session: session),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => RegisterScreen(session: session),
      ),
      GoRoute(
        path: '/verify-email',
        builder: (context, state) => VerifyEmailScreen(
          session: session,
          initialTenant:
              state.uri.queryParameters['empresa_slug'] ?? session.tenant,
          initialToken: state.uri.queryParameters['token'] ?? '',
        ),
      ),
      GoRoute(
        path: '/profile',
        builder: (context, state) => ProfileScreen(session: session),
      ),
    ],
  );
}
