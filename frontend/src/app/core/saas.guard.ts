import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from './auth.service';

export const superadminGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const user = auth.user();

  if (!auth.isAuthenticated()) {
    return router.createUrlTree(['/login']);
  }
  return user?.rol === 'superadmin' && !user.empresa_id
    ? true
    : router.createUrlTree(['/profile']);
};

export const tenantAdminGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const user = auth.user();

  if (!auth.isAuthenticated()) {
    return router.createUrlTree(['/login']);
  }
  return user?.rol === 'administrador' && !!user.empresa_id
    ? true
    : router.createUrlTree(['/profile']);
};
