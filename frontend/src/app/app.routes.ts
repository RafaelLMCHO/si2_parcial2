import { Routes } from '@angular/router';

import { authGuard, guestGuard } from './core/auth.guard';
import { adminOrSuperadminGuard, superadminGuard, tenantAdminGuard } from './core/saas.guard';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'profile',
  },
  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () =>
      import('./features/auth/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'register',
    canActivate: [guestGuard],
    loadComponent: () =>
      import('./features/auth/register/register.component').then((m) => m.RegisterComponent),
  },
  {
    path: 'verify-email',
    canActivate: [guestGuard],
    loadComponent: () =>
      import('./features/auth/verify-email/verify-email.component').then(
        (m) => m.VerifyEmailComponent,
      ),
  },
  {
    path: 'profile',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/profile/profile.component').then((m) => m.ProfileComponent),
  },
  {
    path: 'catalogo',
    loadComponent: () =>
      import('./features/catalogo-cliente/catalogo-cliente.component').then(
        (m) => m.CatalogoClienteComponent,
      ),
  },
  {
    path: 'catalogo/:id',
    loadComponent: () =>
      import('./features/catalogo-cliente/detalle-producto/detalle-producto.component').then(
        (m) => m.DetalleProductoComponent,
      ),
  },
  {
    path: 'disponibilidad-tiendas',
    loadComponent: () =>
      import('./features/disponibilidad-tiendas/disponibilidad-tiendas.component').then(
        (m) => m.DisponibilidadTiendasComponent,
      ),
  },
  {
    path: 'mi-suscripcion',
    canActivate: [tenantAdminGuard],
    loadComponent: () =>
      import('./features/mi-suscripcion/mi-suscripcion.component').then(
        (m) => m.MiSuscripcionComponent,
      ),
  },
  {
    path: 'saas',
    canActivate: [superadminGuard],
    loadComponent: () =>
      import('./features/saas/panel/panel.component').then((m) => m.SaasPanelComponent),
  },
  {
    path: 'saas/planes',
    canActivate: [superadminGuard],
    loadComponent: () =>
      import('./features/saas/planes/planes.component').then((m) => m.PlanesComponent),
  },
  {
    path: 'saas/facturacion',
    canActivate: [superadminGuard],
    loadComponent: () =>
      import('./features/saas/facturacion/facturacion.component').then((m) => m.FacturacionComponent),
  },
  {
    path: 'saas/metricas',
    canActivate: [superadminGuard],
    loadComponent: () =>
      import('./features/saas/metricas/metricas.component').then((m) => m.MetricasComponent),
  },
  {
    path: 'saas/empresas/nueva',
    canActivate: [superadminGuard],
    loadComponent: () =>
      import('./features/saas/empresa-form/empresa-form.component').then(
        (m) => m.EmpresaFormComponent,
      ),
  },
  {
    path: 'saas/empresas/:id',
    canActivate: [superadminGuard],
    loadComponent: () =>
      import('./features/saas/empresa-detail/empresa-detail.component').then(
        (m) => m.EmpresaDetailComponent,
      ),
  },
  {
    path: 'inventario',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/inventario/inventario.component').then((m) => m.InventarioComponent),
  },
  {
    path: 'reservas',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/reservas/reservas.component').then((m) => m.ReservasComponent),
  },
  {
    path: 'reservas/nueva',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/reservas/reserva-creacion/reserva-creacion.component').then(
        (m) => m.ReservaCreacionComponent,
      ),
  },
  {
    path: 'reservas/mis-reservas',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/reservas/reserva-cliente/reserva-cliente.component').then(
        (m) => m.ReservaClienteComponent,
      ),
  },
  {
    path: 'reservas/staff',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/reservas/reserva-staff/reserva-staff.component').then(
        (m) => m.ReservaStaffComponent,
      ),
  },
  {
    path: 'checkout',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/checkout/checkout.component').then((m) => m.CheckoutComponent),
  },
  {
    path: 'pos',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/pos/pos.component').then((m) => m.PosComponent),
  },
  {
    path: 'auditoria',
    canActivate: [adminOrSuperadminGuard],
    loadComponent: () =>
      import('./features/auditoria/auditoria.component').then((m) => m.AuditoriaComponent),
  },
  {
    path: 'empleados',
    canActivate: [tenantAdminGuard],
    loadComponent: () =>
      import('./features/empleados/empleados.component').then((m) => m.EmpleadosComponent),
  },
  {
    path: 'sucursales',
    canActivate: [tenantAdminGuard],
    loadComponent: () =>
      import('./features/sucursales/sucursales.component').then((m) => m.SucursalesComponent),
  },
  {
    path: 'catalogo-admin',
    canActivate: [tenantAdminGuard],
    loadComponent: () =>
      import('./features/catalogo-admin/catalogo-admin.component').then((m) => m.CatalogoAdminComponent),
  },
  {
    path: 'proveedores',
    canActivate: [tenantAdminGuard],
    loadComponent: () =>
      import('./features/proveedores/proveedores.component').then((m) => m.ProveedoresComponent),
  },
  {
    path: 'temporadas',
    canActivate: [tenantAdminGuard],
    loadComponent: () =>
      import('./features/temporadas/temporadas.component').then((m) => m.TemporadasComponent),
  },
  {
    path: 'pagos',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/pagos/pagos.component').then((m) => m.PagosComponent),
  },
  {
    path: 'offline/catalogo',
    loadComponent: () =>
      import('./features/offline/catalogo-offline/catalogo-offline.component').then(
        (m) => m.CatalogoOfflineComponent,
      ),
  },
  {
    path: 'offline/reserva',
    loadComponent: () =>
      import('./features/offline/reserva-offline/reserva-offline.component').then(
        (m) => m.ReservaOfflineComponent,
      ),
  },
  {
    path: 'offline/bloqueos',
    loadComponent: () =>
      import('./features/offline/bloqueos-activos/bloqueos-activos.component').then(
        (m) => m.BloqueosActivosComponent,
      ),
  },
  {
    path: 'offline/venta',
    loadComponent: () =>
      import('./features/offline/venta-offline/venta-offline.component').then(
        (m) => m.VentaOfflineComponent,
      ),
  },
  {
    path: 'offline/cambio',
    loadComponent: () =>
      import('./features/offline/cambio-qr/cambio-qr.component').then(
        (m) => m.CambioQrComponent,
      ),
  },
  {
    path: 'offline/cola',
    loadComponent: () =>
      import('./features/offline/cola-operaciones/cola-operaciones.component').then(
        (m) => m.ColaOperacionesComponent,
      ),
  },
  {
    path: 'offline/conflictos',
    loadComponent: () =>
      import('./features/offline/conflictos/conflictos.component').then(
        (m) => m.ConflictosSyncComponent,
      ),
  },
  {
    path: 'reportes/convencionales',
    loadComponent: () =>
      import('./features/reportes/reportes-convencionales.component').then(
        (m) => m.ReportesConvencionalesComponent,
      ),
  },
  {
    path: 'reportes/ia',
    loadComponent: () =>
      import('./features/reportes/reporte-ia.component').then(
        (m) => m.ReporteIaComponent,
      ),
  },
  {
    path: 'analytics-ml',
    loadComponent: () =>
      import('./features/analytics-ml/dashboard-ml.component').then(
        (m) => m.DashboardMlComponent,
      ),
  },
  {
    path: 'vestidor-virtual',
    loadComponent: () =>
      import('./features/vestidor-virtual/vestidor-virtual.component').then(
        (m) => m.VestidorVirtualComponent,
      ),
  },
  {
    path: 'saas/backups',
    canActivate: [superadminGuard],
    loadComponent: () =>
      import('./features/backups/backups.component').then((m) => m.BackupsComponent),
  },
  {
    path: 'backups',
    canActivate: [adminOrSuperadminGuard],
    loadComponent: () =>
      import('./features/backups/backups.component').then((m) => m.BackupsComponent),
  },
  {
    path: '**',
    redirectTo: 'login',
  },
];
