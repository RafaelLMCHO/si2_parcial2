import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-saas-facturacion',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="container mx-auto px-4 py-8 max-w-6xl font-sans">
      <div class="flex justify-between items-center mb-6 border-b pb-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">CU-08: Facturación SaaS y Cobros</h1>
          <p class="text-sm text-gray-500">Historial de facturas automáticas generadas por Stripe</p>
        </div>
      </div>

      @if (cargando()) {
        <div class="flex justify-center p-12"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>
      } @else {
        <div class="bg-white border rounded-2xl shadow-sm overflow-hidden">
          <table class="w-full text-left text-sm">
            <thead class="bg-gray-50 border-b text-xs font-semibold text-gray-500 uppercase">
              <tr>
                <th class="px-6 py-3">Número</th>
                <th class="px-6 py-3">Fecha</th>
                <th class="px-6 py-3">Total</th>
                <th class="px-6 py-3">Estado</th>
                <th class="px-6 py-3 text-right">Comprobante</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              @for (f of facturas(); track f.id) {
                <tr class="hover:bg-gray-50">
                  <td class="px-6 py-4 font-mono font-medium">{{ f.numero || f.id.slice(0, 8) }}</td>
                  <td class="px-6 py-4 text-gray-500">{{ f.created_at | date:'short' }}</td>
                  <td class="px-6 py-4 font-bold text-gray-900">BOB {{ f.monto }}</td>
                  <td class="px-6 py-4">
                    <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800">
                      {{ f.estado || 'pagada' }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-right">
                    <button class="text-indigo-600 hover:text-indigo-900 text-xs font-semibold">Descargar PDF</button>
                  </td>
                </tr>
              } @empty {
                <tr><td colspan="5" class="px-6 py-8 text-center text-gray-400">No hay facturas registradas.</td></tr>
              }
            </tbody>
          </table>
        </div>
      }
    </div>
  `
})
export class FacturacionComponent implements OnInit {
  private http = inject(HttpClient);
  cargando = signal(false);
  facturas = signal<any[]>([]);

  ngOnInit() {
    this.cargar();
  }

  cargar() {
    this.cargando.set(true);
    this.http.get<any>('/api/v1/saas/facturas').subscribe({
      next: (res) => {
        this.facturas.set(Array.isArray(res) ? res : (res.items || []));
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false)
    });
  }
}

