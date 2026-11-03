import { Injectable } from '@angular/core';

import { LoginResponse, User } from './models';

@Injectable({ providedIn: 'root' })
export class SessionStoreService {
  private readonly accessKey = 'fs_access_token';
  private readonly refreshKey = 'fs_refresh_token';
  private readonly userKey = 'fs_user';
  private readonly tenantKey = 'fs_tenant';
  private readonly expiresKey = 'fs_expires_at';

  readAccessToken(): string | null {
    return this.read(this.accessKey);
  }

  readRefreshToken(): string | null {
    return this.read(this.refreshKey);
  }

  readUser(): User | null {
    const raw = this.read(this.userKey);
    if (!raw) {
      return null;
    }

    try {
      return JSON.parse(raw) as User;
    } catch {
      return null;
    }
  }

  readExpiresAt(): number | null {
    const raw = this.read(this.expiresKey);
    if (!raw) {
      return null;
    }

    const value = Number(raw);
    return Number.isFinite(value) ? value : null;
  }

  readTenant(): string {
    return this.read(this.tenantKey) ?? 'demo';
  }

  saveSession(response: LoginResponse): void {
    this.write(this.accessKey, response.access_token);
    this.write(this.refreshKey, response.refresh_token);
    this.write(this.userKey, JSON.stringify(response.usuario));
    this.write(this.expiresKey, String(Date.now() + response.expires_in * 1000));
  }

  saveTokens(accessToken: string, refreshToken: string, expiresIn: number): void {
    this.write(this.accessKey, accessToken);
    this.write(this.refreshKey, refreshToken);
    this.write(this.expiresKey, String(Date.now() + expiresIn * 1000));
  }

  saveUser(user: User): void {
    this.write(this.userKey, JSON.stringify(user));
  }

  saveTenant(slug: string): void {
    this.write(this.tenantKey, slug);
  }

  clearAuth(): void {
    this.remove(this.accessKey);
    this.remove(this.refreshKey);
    this.remove(this.userKey);
    this.remove(this.expiresKey);
  }

  private read(key: string): string | null {
    if (typeof localStorage === 'undefined') {
      return null;
    }
    return localStorage.getItem(key);
  }

  private write(key: string, value: string): void {
    if (typeof localStorage === 'undefined') {
      return;
    }
    localStorage.setItem(key, value);
  }

  private remove(key: string): void {
    if (typeof localStorage === 'undefined') {
      return;
    }
    localStorage.removeItem(key);
  }
}
