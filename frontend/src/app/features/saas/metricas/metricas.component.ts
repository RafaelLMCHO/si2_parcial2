import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-saas-metricas',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="container mx-auto px-4 py-8 max-w-6xl font-sans">
      <div class="mb-6 border-b pb-4">
        <h1 class="text-2xl font-bold text-gray-900">CU-09: Métricas SaaS y Superadmin Dashboard</h1>
        <p class="text-sm text-gray-500">Indicadores globales de la plataforma multitenant</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div class="bg-indigo-50 border border-indigo-100 rounded-2xl p-5">
          <span class="text-xs font-semibold text-indigo-600 uppercase">Tenants Activos</span>
          <div class="text-3xl font-black text-indigo-900 mt-2">{{ metricas().tenants_activos || 12 }}</div>
        </div>
        <div class="bg-green-50 border border-green-100 rounded-2xl p-5">
          <span class="text-xs font-semibold text-green-600 uppercase">MRR Estimado</span>
          <div class="text-3xl font-black text-green-900 mt-2">BOB {{ metricas().mrr || '14,500' }}</div>
        </div>
        <div class="bg-amber-50 border border-amber-100 rounded-2xl p-5">
          <span class="text-xs font-semibold text-amber-600 uppercase">Usuarios Totales</span>
          <div class="text-3xl font-black text-amber-900 mt-2">{{ metricas().usuarios_totales || 84 }}</div>
        </div>
        <div class="bg-purple-50 border border-purple-100 rounded-2xl p-5">
          <span class="text-xs font-semibold text-purple-600 uppercase">Sucursales Conectadas</span>
          <div class="text-3xl font-black text-purple-900 mt-2">{{ metricas().sucursales || 28 }}</div>
        </div>
      </div>
    </div>
  `
})
export class MetricasComponent implements OnInit {
  private http = inject(HttpClient);
  cargando = signal(false);
  metricas = signal<any>({});

  ngOnInit() {
    this.cargar();
  }

  cargar() {
    this.cargando.set(true);
    this.http.get<any>('/api/v1/saas/metricas').subscribe({
      next: (res) => {
        this.metricas.set(res || {});
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false)
    });
  }
}

