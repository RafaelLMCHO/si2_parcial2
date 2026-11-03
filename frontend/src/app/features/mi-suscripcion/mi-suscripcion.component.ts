import { DatePipe, DecimalPipe, KeyValuePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { apiErrorMessage } from '../../core/error-mapper';
import { MiSuscripcionResponse } from '../../core/models';
import { NetworkService } from '../../core/network.service';
import { SaasService } from '../../core/saas.service';

@Component({
  selector: 'app-mi-suscripcion',
  imports: [RouterLink, DatePipe, DecimalPipe, KeyValuePipe],
  templateUrl: './mi-suscripcion.component.html',
  styleUrl: './mi-suscripcion.component.css',
})
export class MiSuscripcionComponent implements OnInit {
  private readonly saas = inject(SaasService);
  readonly network = inject(NetworkService);

  readonly data = signal<MiSuscripcionResponse | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    if (!this.network.online()) {
      this.error.set('Sin conexion. No se puede consultar la suscripcion.');
      return;
    }

    this.loading.set(true);
    this.error.set(null);
    this.saas
      .miSuscripcion()
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (data) => this.data.set(data),
        error: (error) =>
          this.error.set(apiErrorMessage(error, 'No se pudo consultar la suscripcion.')),
      });
  }

  limiteLabel(recurso: string): string {
    const labels: Record<string, string> = {
      sucursales: 'Sucursales',
      usuarios: 'Usuarios',
      productos: 'Productos',
      consultas_ia_mes: 'Consultas IA / mes',
    };
    return labels[recurso] ?? recurso;
  }
}
