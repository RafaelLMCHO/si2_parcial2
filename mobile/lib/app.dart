import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'core/session/session_controller.dart';
import 'core/theme/app_theme.dart';

class FashionStoreApp extends StatelessWidget {
  const FashionStoreApp({
    super.key,
    required this.session,
    required this.router,
  });

  final SessionController session;
  final GoRouter router;

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'FashionStore',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      routerConfig: router,
    );
  }
}
