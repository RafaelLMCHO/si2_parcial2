import 'package:go_router/go_router.dart';

import '../../features/auditoria/presentation/auditoria_screen.dart';
import '../../features/auth/presentation/login_screen.dart';
import '../../features/auth/presentation/register_screen.dart';
import '../../features/auth/presentation/verify_email_screen.dart';
import '../../features/catalogo/presentation/catalogo_controller.dart';
import '../../features/catalogo/presentation/catalogo_screen.dart';
import '../../features/catalogo_admin/presentation/catalogo_admin_screen.dart';
import '../../features/checkout/presentation/checkout_screen.dart';
import '../../features/empleados/presentation/empleados_screen.dart';
import '../../features/inventario/presentation/disponibilidad_screen.dart';
import '../../features/inventario/presentation/inventario_screen.dart';
import '../../features/offline/presentation/catalogo_offline_screen.dart';
import '../../features/offline/presentation/reserva_offline_screen.dart';
import '../../features/offline/presentation/venta_offline_screen.dart';
import '../../features/offline/presentation/cambio_qr_screen.dart';
import '../../features/offline/presentation/cola_operaciones_screen.dart';
import '../../features/offline/presentation/conflictos_screen.dart';
import '../../features/reportes/presentation/reportes_convencionales_screen.dart';
import '../../features/reportes/presentation/reporte_ia_screen.dart';
import '../../features/analytics_ml/presentation/dashboard_ml_screen.dart';
import '../../features/vestidor_virtual/presentation/vestidor_virtual_screen.dart';
import '../../features/pagos/presentation/pagos_screen.dart';
import '../../features/pos/presentation/pos_screen.dart';
import '../../features/profile/presentation/profile_screen.dart';
import '../../features/proveedores/presentation/proveedores_screen.dart';
import '../../features/reservas/presentation/reservas_screen.dart';
import '../../features/saas/presentation/saas_screen.dart';
import '../../features/sucursales/presentation/sucursales_screen.dart';
import '../../features/temporadas/presentation/temporadas_screen.dart';
import '../session/session_controller.dart';

GoRouter createRouter(
  SessionController session,
  CatalogoController catalogoController,
) {
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
      GoRoute(
        path: '/catalogo',
        builder: (context, state) =>
            CatalogoScreen(session: session, controller: catalogoController),
      ),
      GoRoute(
        path: '/inventario',
        builder: (context, state) =>
            InventarioScreen(apiClient: session.apiClient),
      ),
      GoRoute(
        path: '/disponibilidad',
        builder: (context, state) =>
            DisponibilidadScreen(apiClient: session.apiClient),
      ),
      GoRoute(
        path: '/reservas',
        builder: (context, state) =>
            ReservasScreen(apiClient: session.apiClient, esEncargado: session.user?.rol == 'encargado'),
      ),
      GoRoute(
        path: '/checkout',
        builder: (context, state) =>
            CheckoutScreen(apiClient: session.apiClient),
      ),
      GoRoute(
        path: '/pos',
        builder: (context, state) =>
            PosScreen(apiClient: session.apiClient),
      ),
      GoRoute(
        path: '/pagos',
        builder: (context, state) =>
            PagosScreen(apiClient: session.apiClient),
      ),
      GoRoute(
        path: '/auditoria',
        builder: (context, state) =>
            AuditoriaScreen(apiClient: session.apiClient),
      ),
      GoRoute(
        path: '/empleados',
        builder: (context, state) =>
            EmpleadosScreen(apiClient: session.apiClient),
      ),
      GoRoute(
        path: '/sucursales',
        builder: (context, state) =>
            SucursalesScreen(apiClient: session.apiClient),
      ),
      GoRoute(
        path: '/catalogo-admin',
        builder: (context, state) =>
            CatalogoAdminScreen(apiClient: session.apiClient),
      ),
      GoRoute(
        path: '/proveedores',
        builder: (context, state) =>
            ProveedoresScreen(apiClient: session.apiClient),
      ),
      GoRoute(
        path: '/temporadas',
        builder: (context, state) =>
            TemporadasScreen(apiClient: session.apiClient),
      ),
      GoRoute(
        path: '/saas',
        builder: (context, state) =>
            SaasScreen(apiClient: session.apiClient),
      ),
      GoRoute(
        path: '/offline/catalogo',
        builder: (context, state) =>
            CatalogoOfflineScreen(apiClient: session.apiClient, database: session.database),
      ),
      GoRoute(
        path: '/offline/reserva',
        builder: (context, state) =>
            ReservaOfflineScreen(database: session.database),
      ),
      GoRoute(
        path: '/offline/venta',
        builder: (context, state) =>
            VentaOfflineScreen(database: session.database),
      ),
      GoRoute(
        path: '/offline/cambio',
        builder: (context, state) =>
            CambioQrScreen(database: session.database),
      ),
      GoRoute(
        path: '/offline/cola',
        builder: (context, state) =>
            ColaOperacionesScreen(apiClient: session.apiClient, database: session.database),
      ),
      GoRoute(
        path: '/offline/conflictos',
        builder: (context, state) =>
            ConflictosScreen(apiClient: session.apiClient),
      ),
      GoRoute(
        path: '/reportes/convencionales',
        builder: (context, state) =>
            ReportesConvencionalesScreen(session: session),
      ),
      GoRoute(
        path: '/reportes/ia',
        builder: (context, state) =>
            ReporteIaScreen(session: session),
      ),
      GoRoute(
        path: '/analytics-ml',
        builder: (context, state) =>
            DashboardMlScreen(session: session),
      ),
      GoRoute(
        path: '/vestidor-virtual',
        builder: (context, state) =>
            VestidorVirtualScreen(session: session),
      ),
    ],
  );
}
