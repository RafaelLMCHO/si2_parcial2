import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from './auth.service';

export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  return auth.isAuthenticated() ? true : router.createUrlTree(['/login']);
};

export const guestGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const user = auth.user();
  if (!auth.isAuthenticated()) {
    return true;
  }
  return user?.rol === 'superadmin' && !user.empresa_id
    ? router.createUrlTree(['/saas'])
    : router.createUrlTree(['/profile']);
};
