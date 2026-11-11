import 'package:flutter/material.dart';

class ModuloApp {
  const ModuloApp({
    required this.route,
    required this.label,
    required this.icon,
  });

  final String route;
  final String label;
  final IconData icon;
}

String _normalizeRole(String? rol) => (rol ?? '').trim().toLowerCase();

String _normalizeRoute(String location) {
  final path = Uri.tryParse(location)?.path ?? location;
  if (path.startsWith('/catalogo/prenda/')) {
    return '/catalogo/prenda/:id';
  }
  return path;
}

const Set<String> _publicAndCommonRoutes = {
  '/login',
  '/register',
  '/verify-email',
  '/profile',
};

const Map<String, Set<String>> _allowedRoutesByRole = {
  'superadmin': {
    '/profile',
    '/saas',
    '/auditoria',
    '/backups',
  },
  'administrador': {
    '/profile',
    '/catalogo',
    '/catalogo/prenda/:id',
    '/disponibilidad',
    '/catalogo-admin',
    '/inventario',
    '/reservas',
    '/pos',
    '/checkout',
    '/pagos',
    '/sucursales',
    '/empleados',
    '/proveedores',
    '/temporadas',
    '/reportes/convencionales',
    '/reportes/ia',
    '/analytics-ml',
    '/vestidor-virtual',
    '/backups',
    '/auditoria',
    '/offline/catalogo',
    '/offline/bloqueos',
    '/offline/reserva',
    '/offline/venta',
    '/offline/cambio',
    '/offline/cola',
    '/offline/conflictos',
  },
  'encargado': {
    '/profile',
    '/catalogo',
    '/catalogo/prenda/:id',
    '/disponibilidad',
    '/inventario',
    '/reservas',
    '/pos',
    '/vestidor-virtual',
    '/offline/catalogo',
    '/offline/bloqueos',
    '/offline/reserva',
    '/offline/cola',
    '/offline/conflictos',
  },
  'cajero': {
    '/profile',
    '/catalogo',
    '/catalogo/prenda/:id',
    '/disponibilidad',
    '/inventario',
    '/pos',
    '/pagos',
    '/vestidor-virtual',
    '/offline/catalogo',
    '/offline/bloqueos',
    '/offline/venta',
    '/offline/cambio',
    '/offline/cola',
  },
  'cliente': {
    '/profile',
    '/catalogo',
    '/catalogo/prenda/:id',
    '/disponibilidad',
    '/checkout',
    '/reservas',
    '/vestidor-virtual',
  },
};

bool canAccessRoute(String? rol, String location) {
  final normalizedRoute = _normalizeRoute(location);
  if (_publicAndCommonRoutes.contains(normalizedRoute)) {
    return true;
  }
  final allowed = _allowedRoutesByRole[_normalizeRole(rol)];
  if (allowed == null) {
    return false;
  }
  return allowed.contains(normalizedRoute);
}

List<ModuloApp> modulesForRole(String? rol) {
  switch (_normalizeRole(rol)) {
    case 'superadmin':
      return const [
        ModuloApp(
          route: '/saas',
          label: 'SaaS',
          icon: Icons.admin_panel_settings,
        ),
        ModuloApp(
          route: '/auditoria',
          label: 'Auditoria',
          icon: Icons.security,
        ),
        ModuloApp(
          route: '/backups',
          label: 'Backups',
          icon: Icons.backup,
        ),
      ];
    case 'administrador':
      return const [
        ModuloApp(
          route: '/catalogo',
          label: 'Catalogo',
          icon: Icons.checkroom,
        ),
        ModuloApp(
          route: '/catalogo-admin',
          label: 'Catalogo Admin',
          icon: Icons.style,
        ),
        ModuloApp(
          route: '/inventario',
          label: 'Inventario',
          icon: Icons.inventory_2,
        ),
        ModuloApp(
          route: '/reservas',
          label: 'Reservas',
          icon: Icons.event_available,
        ),
        ModuloApp(
          route: '/pos',
          label: 'POS',
          icon: Icons.point_of_sale,
        ),
        ModuloApp(
          route: '/sucursales',
          label: 'Sucursales',
          icon: Icons.store,
        ),
        ModuloApp(
          route: '/empleados',
          label: 'Empleados',
          icon: Icons.badge,
        ),
        ModuloApp(
          route: '/proveedores',
          label: 'Proveedores',
          icon: Icons.local_shipping,
        ),
        ModuloApp(
          route: '/temporadas',
          label: 'Temporadas',
          icon: Icons.calendar_today,
        ),
        ModuloApp(
          route: '/reportes/convencionales',
          label: 'Reportes',
          icon: Icons.bar_chart,
        ),
        ModuloApp(
          route: '/reportes/ia',
          label: 'Reporte IA',
          icon: Icons.auto_awesome,
        ),
        ModuloApp(
          route: '/analytics-ml',
          label: 'Analytics ML',
          icon: Icons.analytics,
        ),
        ModuloApp(
          route: '/vestidor-virtual',
          label: 'Vestidor RA',
          icon: Icons.view_in_ar,
        ),
        ModuloApp(
          route: '/offline/catalogo',
          label: 'Catalogo Offline',
          icon: Icons.download_for_offline,
        ),
        ModuloApp(
          route: '/offline/bloqueos',
          label: 'Bloqueos activos',
          icon: Icons.lock_clock,
        ),
        ModuloApp(
          route: '/offline/reserva',
          label: 'Reserva Offline',
          icon: Icons.cloud_off,
        ),
        ModuloApp(
          route: '/offline/venta',
          label: 'Venta Offline',
          icon: Icons.payments_outlined,
        ),
        ModuloApp(
          route: '/offline/cambio',
          label: 'Cambio QR',
          icon: Icons.qr_code_scanner,
        ),
        ModuloApp(
          route: '/offline/cola',
          label: 'Cola Offline',
          icon: Icons.sync,
        ),
        ModuloApp(
          route: '/offline/conflictos',
          label: 'Conflictos Offline',
          icon: Icons.warning_amber,
        ),
        ModuloApp(
          route: '/backups',
          label: 'Backups',
          icon: Icons.backup,
        ),
        ModuloApp(
          route: '/auditoria',
          label: 'Auditoria',
          icon: Icons.security,
        ),
      ];
    case 'encargado':
      return const [
        ModuloApp(
          route: '/reservas',
          label: 'Reservas por Preparar',
          icon: Icons.event_available,
        ),
        ModuloApp(
          route: '/inventario',
          label: 'Inventario',
          icon: Icons.inventory_2,
        ),
        ModuloApp(
          route: '/pos',
          label: 'POS',
          icon: Icons.point_of_sale,
        ),
        ModuloApp(
          route: '/catalogo',
          label: 'Catalogo',
          icon: Icons.checkroom,
        ),
        ModuloApp(
          route: '/vestidor-virtual',
          label: 'Vestidor RA',
          icon: Icons.view_in_ar,
        ),
        ModuloApp(
          route: '/offline/bloqueos',
          label: 'Bloqueos activos',
          icon: Icons.lock_clock,
        ),
        ModuloApp(
          route: '/offline/reserva',
          label: 'Reserva Offline',
          icon: Icons.cloud_off,
        ),
        ModuloApp(
          route: '/offline/cola',
          label: 'Cola Offline',
          icon: Icons.sync,
        ),
        ModuloApp(
          route: '/offline/conflictos',
          label: 'Conflictos Offline',
          icon: Icons.warning_amber,
        ),
      ];
    case 'cajero':
      return const [
        ModuloApp(
          route: '/pos',
          label: 'POS',
          icon: Icons.point_of_sale,
        ),
        ModuloApp(
          route: '/inventario',
          label: 'Inventario',
          icon: Icons.inventory_2,
        ),
        ModuloApp(
          route: '/catalogo',
          label: 'Catalogo',
          icon: Icons.checkroom,
        ),
        ModuloApp(
          route: '/vestidor-virtual',
          label: 'Vestidor RA',
          icon: Icons.view_in_ar,
        ),
        ModuloApp(
          route: '/offline/bloqueos',
          label: 'Bloqueos activos',
          icon: Icons.lock_clock,
        ),
        ModuloApp(
          route: '/offline/venta',
          label: 'Venta Offline',
          icon: Icons.payments_outlined,
        ),
        ModuloApp(
          route: '/offline/cambio',
          label: 'Cambio QR',
          icon: Icons.qr_code_scanner,
        ),
        ModuloApp(
          route: '/offline/cola',
          label: 'Cola Offline',
          icon: Icons.sync,
        ),
      ];
    case 'cliente':
      return const [
        ModuloApp(
          route: '/catalogo',
          label: 'Catalogo',
          icon: Icons.checkroom,
        ),
        ModuloApp(
          route: '/checkout',
          label: 'Carrito y Checkout',
          icon: Icons.shopping_bag,
        ),
        ModuloApp(
          route: '/reservas',
          label: 'Mis Reservas',
          icon: Icons.event_available,
        ),
        ModuloApp(
          route: '/vestidor-virtual',
          label: 'Vestidor RA',
          icon: Icons.view_in_ar,
        ),
      ];
    default:
      return const [];
  }
}

