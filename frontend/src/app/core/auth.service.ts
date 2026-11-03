import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { EMPTY, Observable, catchError, finalize, tap, throwError } from 'rxjs';

import { environment } from '../../environments/environment';
import {
  LoginResponse,
  RefreshResponse,
  RegisterResponse,
  User,
  VerifyEmailResponse,
} from './models';
import { NetworkService } from './network.service';
import { OfflineQueueService } from './offline-queue.service';
import { SessionStoreService } from './session-store.service';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly offline = inject(OfflineQueueService);
  private readonly store = inject(SessionStoreService);
  private readonly network = inject(NetworkService);
  private readonly apiUrl = environment.apiUrl;

  readonly user = signal<User | null>(this.store.readUser());
  readonly accessToken = signal<string | null>(this.store.readAccessToken());
  readonly refreshToken = signal<string | null>(this.store.readRefreshToken());
  readonly expiresAt = signal<number | null>(this.store.readExpiresAt());
  readonly isAuthenticated = computed(() => !!this.accessToken() && !!this.user());
  readonly pendingOffline = signal(this.offline.hasPending());
  readonly canWrite = computed(
    () => this.network.online() && this.isAuthenticated() && !this.isSessionExpired(),
  );

  login(payload: {
    empresa_slug: string | null;
    correo: string;
    password: string;
  }): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.apiUrl}/auth/login`, payload).pipe(
      tap((response) => {
        this.storeSession(response);
        if (payload.empresa_slug) {
          this.store.saveTenant(payload.empresa_slug);
        }
        this.network.markOnline();
      }),
    );
  }

  register(payload: {
    empresa_slug: string;
    nombre: string;
    correo: string;
    telefono?: string | null;
    password: string;
  }): Observable<RegisterResponse> {
    return this.http.post<RegisterResponse>(`${this.apiUrl}/auth/register`, payload).pipe(
      tap(() => {
        this.store.saveTenant(payload.empresa_slug);
        this.network.markOnline();
      }),
    );
  }

  verifyEmail(payload: {
    empresa_slug: string;
    token: string;
  }): Observable<VerifyEmailResponse> {
    return this.http.post<VerifyEmailResponse>(`${this.apiUrl}/auth/verify-email`, payload).pipe(
      tap(() => this.network.markOnline()),
    );
  }

  refresh(): Observable<RefreshResponse> {
    const refreshToken = this.refreshToken();
    if (!refreshToken) {
      return throwError(() => new Error('No hay token de refresco'));
    }

    return this.http
      .post<RefreshResponse>(`${this.apiUrl}/auth/refresh`, { refresh_token: refreshToken })
      .pipe(
        tap((response) => {
          this.store.saveTokens(
            response.access_token,
            response.refresh_token,
            response.expires_in,
          );
          this.accessToken.set(response.access_token);
          this.refreshToken.set(response.refresh_token);
          this.expiresAt.set(Date.now() + response.expires_in * 1000);
          this.network.markOnline();
        }),
      );
  }

  logout(): Observable<unknown> {
    const token = this.accessToken();
    const request: Observable<unknown> = token
      ? this.http.post(`${this.apiUrl}/auth/logout`, {})
      : EMPTY;

    return request.pipe(
      catchError(() => EMPTY),
      finalize(() => {
        this.clearSession();
        void this.router.navigate(['/login']);
      }),
    );
  }

  me(): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/users/me`).pipe(
      tap((user) => {
        this.store.saveUser(user);
        this.user.set(user);
        this.network.markOnline();
      }),
    );
  }

  updateMe(payload: { nombre?: string | null; telefono?: string | null }): Observable<User> {
    return this.http.patch<User>(`${this.apiUrl}/users/me`, payload).pipe(
      tap((user) => {
        this.store.saveUser(user);
        this.user.set(user);
        this.network.markOnline();
      }),
    );
  }

  changePassword(payload: {
    password_actual: string;
    password_nueva: string;
  }): Observable<{ mensaje: string }> {
    return this.http
      .post<{ mensaje: string }>(`${this.apiUrl}/users/me/password`, payload)
      .pipe(tap(() => this.network.markOnline()));
  }

  tenantSlug(): string {
    return this.store.readTenant();
  }

  isSessionExpired(): boolean {
    const expiresAt = this.expiresAt();
    return expiresAt !== null && Date.now() >= expiresAt;
  }

  clearSession(): void {
    this.store.clearAuth();
    this.accessToken.set(null);
    this.refreshToken.set(null);
    this.expiresAt.set(null);
    this.user.set(null);
    this.pendingOffline.set(this.offline.hasPending());
  }

  private storeSession(response: LoginResponse): void {
    this.store.saveSession(response);
    this.accessToken.set(response.access_token);
    this.refreshToken.set(response.refresh_token);
    this.expiresAt.set(Date.now() + response.expires_in * 1000);
    this.user.set(response.usuario);
    this.pendingOffline.set(this.offline.hasPending());
  }
}
