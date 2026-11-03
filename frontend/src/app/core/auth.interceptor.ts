import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, catchError, finalize, switchMap, tap, throwError } from 'rxjs';

import { AuthService } from './auth.service';
import { isNetworkError } from './error-mapper';
import { RefreshResponse } from './models';
import { NetworkService } from './network.service';

let refreshInProgress: Observable<RefreshResponse> | null = null;

const AUTH_ENDPOINTS = ['/auth/login', '/auth/register', '/auth/refresh', '/auth/verify-email'];

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const network = inject(NetworkService);
  const isAuthCall = AUTH_ENDPOINTS.some((endpoint) => request.url.includes(endpoint));
  const token = auth.accessToken();

  const authenticatedRequest =
    token && !isAuthCall
      ? request.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
      : request;

  return next(authenticatedRequest).pipe(
    tap(() => network.markOnline()),
    catchError((error: HttpErrorResponse) => {
      if (isNetworkError(error)) {
        network.markOffline();
        return throwError(() => error);
      }

      if (error.status !== 401 || isAuthCall) {
        return throwError(() => error);
      }

      const refreshToken = auth.refreshToken();
      if (!refreshToken) {
        auth.clearSession();
        void router.navigate(['/login']);
        return throwError(() => error);
      }

      if (!refreshInProgress) {
        refreshInProgress = auth.refresh().pipe(
          finalize(() => {
            refreshInProgress = null;
          }),
        );
      }

      return refreshInProgress.pipe(
        switchMap((response) =>
          next(
            request.clone({
              setHeaders: { Authorization: `Bearer ${response.access_token}` },
            }),
          ),
        ),
        catchError((refreshError) => {
          if (isNetworkError(refreshError)) {
            network.markOffline();
            return throwError(() => refreshError);
          }

          auth.clearSession();
          void router.navigate(['/login']);
          return throwError(() => refreshError);
        }),
      );
    }),
  );
};
