import 'package:fashionstore_mobile/app.dart';
import 'package:fashionstore_mobile/core/network/api_client.dart';
import 'package:fashionstore_mobile/core/session/session_controller.dart';
import 'package:fashionstore_mobile/core/storage/local_database.dart';
import 'package:fashionstore_mobile/core/storage/secure_session_store.dart';
import 'package:fashionstore_mobile/core/utils/network_status.dart';
import 'package:fashionstore_mobile/features/auth/data/auth_repository.dart';
import 'package:fashionstore_mobile/features/auth/presentation/login_screen.dart';
import 'package:fashionstore_mobile/features/profile/data/profile_repository.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

SessionController _buildSession() {
  final apiClient = ApiClient(baseUrl: 'http://127.0.0.1:8000/api/v1');
  final network = NetworkStatus()..markOnline();
  final session = SessionController(
    authRepository: AuthRepository(apiClient.dio),
    profileRepository: ProfileRepository(apiClient.dio),
    secureStore: SecureSessionStore(),
    database: LocalDatabase(),
    networkStatus: network,
  );
  apiClient.tokenProvider = () => session.accessToken;
  apiClient.refreshHandler = session.refreshTokens;
  apiClient.sessionExpiredHandler = session.handleSessionExpired;
  apiClient.networkLostHandler = session.handleNetworkLost;
  return session;
}

void main() {
  testWidgets('el login exige correo y contrasena validos', (tester) async {
    final session = _buildSession();

    await tester.pumpWidget(MaterialApp(home: LoginScreen(session: session)));

    expect(find.text('Iniciar sesion'), findsOneWidget);

    await tester.tap(find.text('Ingresar'));
    await tester.pump();

    expect(find.text('Ingrese su correo.'), findsOneWidget);
    expect(find.text('Minimo 8 caracteres.'), findsOneWidget);
  });

  testWidgets('la app muestra el login cuando no hay sesion', (tester) async {
    final session = _buildSession();
    final router = createTestRouter(session);

    await tester.pumpWidget(FashionStoreApp(session: session, router: router));
    await tester.pumpAndSettle();

    expect(find.text('Iniciar sesion'), findsOneWidget);
  });
}

GoRouter createTestRouter(SessionController session) {
  return GoRouter(
    initialLocation: '/login',
    refreshListenable: session,
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => LoginScreen(session: session),
      ),
      GoRoute(
        path: '/profile',
        builder: (context, state) =>
            const Scaffold(body: Text('Perfil de prueba')),
      ),
    ],
  );
}
