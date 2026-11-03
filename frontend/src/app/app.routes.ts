import { Routes } from '@angular/router';

import { authGuard, guestGuard } from './core/auth.guard';
import { superadminGuard, tenantAdminGuard } from './core/saas.guard';

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
    path: '**',
    redirectTo: 'login',
  },
];
