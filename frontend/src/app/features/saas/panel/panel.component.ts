import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { apiErrorMessage } from '../../../core/error-mapper';
import { EmpresaResumen, MetricasSaaS, Plan } from '../../../core/models';
import { NetworkService } from '../../../core/network.service';
import { SaasService } from '../../../core/saas.service';

@Component({
  selector: 'app-saas-panel',
  imports: [ReactiveFormsModule, RouterLink, DatePipe, DecimalPipe],
  templateUrl: './panel.component.html',
  styleUrl: './panel.component.css',
})
export class SaasPanelComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly saas = inject(SaasService);
  readonly network = inject(NetworkService);

  readonly metricas = signal<MetricasSaaS | null>(null);
  readonly empresas = signal<EmpresaResumen[]>([]);
  readonly planes = signal<Plan[]>([]);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly pageSize = 10;
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  readonly filters = this.fb.nonNullable.group({
    search: [''],
    estado: [''],
    plan: [''],
    por_vencer: [false],
  });

  ngOnInit(): void {
    this.loadMetricas();
    this.loadPlanes();
    this.loadEmpresas();
  }

  loadMetricas(): void {
    this.saas.getMetricas().subscribe({
      next: (metricas) => this.metricas.set(metricas),
      error: (error) => this.error.set(apiErrorMessage(error, 'No se pudieron cargar las metricas.')),
    });
  }

  loadPlanes(): void {
    this.saas.listPlanes().subscribe({
      next: (planes) => this.planes.set(planes),
    });
  }

  loadEmpresas(): void {
    if (!this.network.online()) {
      this.error.set('Sin conexion. No se puede consultar el panel SaaS.');
      return;
    }

    const raw = this.filters.getRawValue();
    this.loading.set(true);
    this.error.set(null);
    this.saas
      .listEmpresas({
        search: raw.search.trim() || undefined,
        estado: raw.estado || undefined,
        plan: raw.plan || undefined,
        por_vencer: raw.por_vencer,
        page: this.page(),
        page_size: this.pageSize,
      })
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (response) => {
          this.empresas.set(response.items);
          this.total.set(response.total);
        },
        error: (error) => this.error.set(apiErrorMessage(error, 'No se pudieron cargar las empresas.')),
      });
  }

  applyFilters(): void {
    this.page.set(1);
    this.loadEmpresas();
  }

  clearFilters(): void {
    this.filters.reset({
      search: '',
      estado: '',
      plan: '',
      por_vencer: false,
    });
    this.page.set(1);
    this.loadEmpresas();
  }

  previousPage(): void {
    if (this.page() <= 1) return;
    this.page.set(this.page() - 1);
    this.loadEmpresas();
  }

  nextPage(): void {
    if (this.page() * this.pageSize >= this.total()) return;
    this.page.set(this.page() + 1);
    this.loadEmpresas();
  }

  totalPages(): number {
    return Math.max(1, Math.ceil(this.total() / this.pageSize));
  }
}
