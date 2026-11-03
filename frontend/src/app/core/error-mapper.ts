import { HttpErrorResponse } from '@angular/common/http';

export function isNetworkError(error: unknown): boolean {
  return error instanceof HttpErrorResponse && (error.status === 0 || error.status === -1);
}

export function apiErrorMessage(error: unknown, fallback: string): string {
  if (isNetworkError(error)) {
    return 'Sin conexion. Revise su red e intente nuevamente.';
  }

  if (error instanceof HttpErrorResponse) {
    const detail = error.error?.detail;
    if (detail?.message) {
      return detail.message;
    }

    if (error.status === 402) {
      return 'La empresa no tiene una suscripcion activa.';
    }

    if (error.status === 403) {
      return 'La cuenta no esta habilitada para esta operacion.';
    }

    if (error.status === 429) {
      return 'Demasiados intentos. Espere unos minutos e intente nuevamente.';
    }
  }

  return fallback;
}
