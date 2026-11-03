import 'package:flutter/material.dart';

import 'app.dart';
import 'core/network/api_client.dart';
import 'core/routing/app_router.dart';
import 'core/session/session_controller.dart';
import 'core/storage/local_database.dart';
import 'core/storage/secure_session_store.dart';
import 'core/utils/network_status.dart';
import 'features/auth/data/auth_repository.dart';
import 'features/profile/data/profile_repository.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  try {
    final apiClient = ApiClient();
    final networkStatus = NetworkStatus();
    await networkStatus.init();
    final database = LocalDatabase();
    await database.open();

    final session = SessionController(
      authRepository: AuthRepository(apiClient.dio),
      profileRepository: ProfileRepository(apiClient.dio),
      secureStore: SecureSessionStore(),
      database: database,
      networkStatus: networkStatus,
    );

    apiClient.tokenProvider = () => session.accessToken;
    apiClient.refreshHandler = session.refreshTokens;
    apiClient.sessionExpiredHandler = session.handleSessionExpired;
    apiClient.networkLostHandler = session.handleNetworkLost;

    await session.bootstrap();
    final router = createRouter(session);

    runApp(FashionStoreApp(session: session, router: router));
  } catch (error) {
    runApp(_StartupErrorApp(message: error.toString()));
  }
}

class _StartupErrorApp extends StatelessWidget {
  const _StartupErrorApp({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: Scaffold(
        body: SafeArea(
          child: Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.error_outline, size: 44),
                  const SizedBox(height: 12),
                  const Text(
                    'No se pudo iniciar la aplicacion.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 8),
                  Text(message, textAlign: TextAlign.center),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
