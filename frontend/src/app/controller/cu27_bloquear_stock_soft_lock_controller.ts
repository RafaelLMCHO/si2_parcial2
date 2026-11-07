import { Injectable, signal } from '@angular/core';

/**
 * Controlador Web para CU-27: Bloquear Stock Local Offline con TTL (45 minutos)
 */
@Injectable({ providedIn: 'root' })
export class CU27BloquearStockSoftLockController {
  cargando = signal(false);
  error = signal<string | null>(null);
  locks = signal<Record<string, number>>({});

  bloquearStock(varianteId: string, cantidad: number, ttlMinutos: number = 45): boolean {
    this.cargando.set(true);
    this.error.set(null);

    try {
      const expiraEn = new Date(Date.now() + ttlMinutos * 60 * 1000).toISOString();
      const rawLocks = JSON.parse(localStorage.getItem('soft_locks_locales') || '[]');
      
      // Limpiar locks expirados
      const activos = rawLocks.filter((l: any) => new Date(l.expira_en) > new Date());
      activos.push({
        id: 'lock-' + Date.now(),
        variante_id: varianteId,
        cantidad,
        expira_en: expiraEn,
        creado_en: new Date().toISOString()
      });

      localStorage.setItem('soft_locks_locales', JSON.stringify(activos));

      const updatedMap = { ...this.locks() };
      updatedMap[varianteId] = (updatedMap[varianteId] || 0) + cantidad;
      this.locks.set(updatedMap);
      this.cargando.set(false);
      return true;
    } catch (e: any) {
      this.cargando.set(false);
      this.error.set('Error aplicando soft-lock local: ' + e.message);
      return false;
    }
  }
}

