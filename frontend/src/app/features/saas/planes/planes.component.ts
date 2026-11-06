import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-saas-planes',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="container mx-auto px-4 py-8 max-w-6xl font-sans">
      <div class="flex justify-between items-center mb-6 border-b pb-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">CU-06: Gestión de Planes SaaS</h1>
          <p class="text-sm text-gray-500">Configuración de suscripciones, límites y precios multi-tenant</p>
        </div>
        <button (click)="cargar()" class="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-sm font-semibold rounded-lg">
          Actualizar
        </button>
      </div>

      @if (cargando()) {
        <div class="flex justify-center p-12"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>
      } @else {
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          @for (p of planes(); track p.id) {
            <div class="bg-white border rounded-2xl p-6 shadow-sm flex flex-col justify-between">
              <div>
                <h3 class="text-xl font-bold text-gray-900 mb-2">{{ p.nombre }}</h3>
                <div class="text-2xl font-black text-indigo-600 mb-4">BOB {{ p.precio_mensual }}<span class="text-xs text-gray-400 font-normal">/mes</span></div>
                <ul class="text-xs text-gray-600 space-y-2 mb-6">
                  <li>• Límite sucursales: {{ p.limite_sucursales }}</li>
                  <li>• Límite usuarios: {{ p.limite_usuarios }}</li>
                  <li>• Catálogo prendas: {{ p.limite_prendas }}</li>
                </ul>
              </div>
              <button class="w-full py-2 bg-indigo-50 text-indigo-700 font-bold rounded-xl text-xs hover:bg-indigo-100">
                Editar Plan
              </button>
            </div>
          }
        </div>
      }
    </div>
  `
})
export class PlanesComponent implements OnInit {
  private http = inject(HttpClient);
  cargando = signal(false);
  planes = signal<any[]>([]);

  ngOnInit() {
    this.cargar();
  }

  cargar() {
    this.cargando.set(true);
    this.http.get<any>('/api/v1/saas/planes').subscribe({
      next: (res) => {
        this.planes.set(Array.isArray(res) ? res : (res.items || []));
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false)
    });
  }
}

