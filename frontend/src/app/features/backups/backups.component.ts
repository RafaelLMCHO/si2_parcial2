import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  BackupConfiguracion,
  BackupCreateRequest,
  BackupEstadisticas,
  BackupModuloInfo,
  BackupRegistro,
  CU37GestionBackupsController,
} from '../../controller/cu37_gestion_backups_controller';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-backups',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="backups-page">
      <!-- HEADER -->
      <div class="header-container">
        <div>
          <h2>Copias de Seguridad & Respaldo Híbrido (CU-37)</h2>
          <p class="subtitle">
            Gestión de copias de seguridad personalizadas, automáticas y manuales con visibilidad y
            almacenamiento en <strong>Localhost</strong> y en la <strong>Nube (AWS S3)</strong>.
          </p>
        </div>
        <div class="role-pill">
          <span class="role-badge" [ngClass]="isSuperadmin ? 'badge-super' : 'badge-admin'">
            {{ isSuperadmin ? 'Superadministrador SaaS (Global)' : 'Administrador de Empresa' }}
          </span>
          <span class="tenant-name" *ngIf="user()?.empresa_id">
            Empresa ID: <code>{{ user()?.empresa_id }}</code>
          </span>
        </div>
      </div>

      <!-- ALERTAS Y MENSAJES -->
      <div *ngIf="alertMessage" class="alert-box" [ngClass]="'alert-' + alertType">
        <span>{{ alertMessage }}</span>
        <button type="button" class="alert-close" (click)="alertMessage = null">✕</button>
      </div>

      <!-- DASHBOARD CARDS (ESTADÍSTICAS) -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon icon-backups">📁</div>
          <div class="stat-info">
            <span class="stat-title">Total de Backups</span>
            <span class="stat-number">{{ stats?.total_backups || 0 }}</span>
            <small class="stat-meta">
              {{ stats?.total_manuales || 0 }} manuales · {{ stats?.total_automaticos || 0 }} automáticos
            </small>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon icon-local">💻</div>
          <div class="stat-info">
            <span class="stat-title">Almacenamiento en Localhost</span>
            <span class="stat-number">{{ stats?.espacio_local_legible || '0 B' }}</span>
            <small class="stat-meta text-success">
              ✓ {{ stats?.total_locales || 0 }} disponibles en servidor local
            </small>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon icon-cloud">☁️</div>
          <div class="stat-info">
            <span class="stat-title">Almacenamiento en la Nube</span>
            <span class="stat-number">{{ stats?.espacio_nube_legible || '0 B' }}</span>
            <small class="stat-meta text-primary">
              ✓ {{ stats?.total_nube || 0 }} en {{ stats?.proveedor_nube || 'AWS S3' }}
            </small>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon icon-auto">⏱️</div>
          <div class="stat-info">
            <span class="stat-title">Backup Automático</span>
            <span class="stat-badge" [ngClass]="stats?.auto_backup_activo ? 'badge-on' : 'badge-off'">
              {{ stats?.auto_backup_activo ? 'ACTIVO' : 'INACTIVO' }}
            </span>
            <small class="stat-meta" *ngIf="stats?.proximo_auto_backup">
              Próximo: {{ stats?.proximo_auto_backup | date:'short' }}
            </small>
            <small class="stat-meta" *ngIf="!stats?.proximo_auto_backup">
              Sin ejecución programada
            </small>
          </div>
        </div>
      </div>

      <!-- ACTION BAR & FILTERS -->
      <div class="action-bar">
        <div class="action-buttons">
          <button type="button" class="btn btn-primary" (click)="abrirModalCrear()">
            + Nuevo Backup Personalizado
          </button>
          <button type="button" class="btn btn-secondary" (click)="abrirModalConfig()">
            ⚙ Configurar Backup Automático
          </button>
          <button type="button" class="btn btn-outline" (click)="ejecutarAutoAhora()" [disabled]="ejecutandoAuto">
            {{ ejecutandoAuto ? 'Ejecutando...' : '⚡ Ejecutar Auto Ahora' }}
          </button>
        </div>

        <div class="filter-controls">
          <div class="filter-chips">
            <button
              type="button"
              class="chip"
              [class.chip-active]="filtroDestino === '' && filtroTipo === ''"
              (click)="setFiltro('', '')"
            >
              Todos ({{ backups.length }})
            </button>
            <button
              type="button"
              class="chip"
              [class.chip-active]="filtroDestino === 'local'"
              (click)="setFiltro('local', '')"
            >
              💻 Localhost
            </button>
            <button
              type="button"
              class="chip"
              [class.chip-active]="filtroDestino === 'nube'"
              (click)="setFiltro('nube', '')"
            >
              ☁️ En la Nube
            </button>
            <button
              type="button"
              class="chip"
              [class.chip-active]="filtroTipo === 'automatico'"
              (click)="setFiltro('', 'automatico')"
            >
              ⏱️ Automáticos
            </button>
            <button
              type="button"
              class="chip"
              [class.chip-active]="filtroTipo === 'manual'"
              (click)="setFiltro('', 'manual')"
            >
              ✋ Manuales
            </button>
          </div>

          <div class="search-box">
            <input
              type="text"
              placeholder="Buscar backup..."
              [(ngModel)]="searchQuery"
              (input)="onSearchChange()"
            />
          </div>
        </div>
      </div>

      <!-- TABLA DE COPIAS DE SEGURIDAD -->
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Nombre & Alcance</th>
              <th>Tipo</th>
              <th>Fecha y Hora</th>
              <th>Tamaño / Registros</th>
              <th>Ubicación: Localhost</th>
              <th>Ubicación: Nube (AWS S3)</th>
              <th class="text-right">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let b of backups">
              <td>
                <div class="backup-title">
                  <strong>{{ b.nombre }}</strong>
                  <span class="format-badge" [ngClass]="'fmt-' + b.formato">{{ b.formato | uppercase }}</span>
                </div>
                <div class="backup-sub">
                  <span class="scope-tag" [ngClass]="b.alcance === 'global' ? 'scope-global' : 'scope-empresa'">
                    {{ b.alcance === 'global' ? '🌐 Global SaaS' : ('🏢 ' + (b.empresa_nombre || 'Empresa')) }}
                  </span>
                  <span *ngIf="b.descripcion" class="backup-desc">· {{ b.descripcion }}</span>
                </div>
              </td>

              <td>
                <span class="type-badge" [ngClass]="b.tipo === 'automatico' ? 'type-auto' : 'type-manual'">
                  {{ b.tipo === 'automatico' ? '⏱ Automático' : '✋ Manual' }}
                </span>
              </td>

              <td>
                <div>{{ b.created_at | date:'dd/MM/yyyy HH:mm:ss' }}</div>
                <small class="text-muted" *ngIf="b.usuario_nombre">Por: {{ b.usuario_nombre }}</small>
              </td>

              <td>
                <div><strong>{{ b.tamano_legible }}</strong></div>
                <small class="text-muted">{{ b.total_registros }} registros</small>
              </td>

              <!-- LOCALHOST STATUS & DOWNLOAD -->
              <td>
                <div *ngIf="b.guardado_local" class="storage-cell">
                  <span class="storage-badge badge-local-ok">
                    <span class="dot-ok">●</span> Guardado en Localhost
                  </span>
                  <button
                    type="button"
                    class="btn-icon"
                    title="Descargar copia de Localhost a tu PC"
                    (click)="descargar(b, 'local')"
                  >
                    ⬇ Descargar PC
                  </button>
                </div>
                <div *ngIf="!b.guardado_local">
                  <button
                    type="button"
                    class="btn-sync-action"
                    (click)="sincronizarLocal(b)"
                    title="Descargar de la nube al servidor local"
                  >
                    📥 Traer a Localhost
                  </button>
                </div>
              </td>

              <!-- NUBE (AWS S3) STATUS & DOWNLOAD -->
              <td>
                <div *ngIf="b.guardado_nube" class="storage-cell">
                  <span class="storage-badge badge-cloud-ok">
                    <span class="dot-cloud">☁</span> Sincronizado en Nube
                  </span>
                  <div class="cloud-meta">
                    <small class="cloud-s3-uri" [title]="b.url_nube">{{ b.url_nube }}</small>
                    <button
                      type="button"
                      class="btn-icon btn-cloud-dl"
                      title="Descargar directamente desde la Nube (AWS S3)"
                      (click)="descargar(b, 'cloud')"
                    >
                      ☁ Descargar Nube
                    </button>
                  </div>
                </div>
                <div *ngIf="!b.guardado_nube">
                  <button
                    type="button"
                    class="btn-sync-action btn-sync-cloud"
                    (click)="sincronizarNube(b)"
                    title="Subir y respaldar esta copia en AWS S3"
                  >
                    ☁ Subir a la Nube
                  </button>
                </div>
              </td>

              <!-- ACCIONES -->
              <td class="text-right">
                <div class="action-group">
                  <button
                    type="button"
                    class="action-btn action-view"
                    (click)="abrirModalDetalle(b)"
                    title="Ver detalles e inspeccionar tablas"
                  >
                    🔍 Detalle
                  </button>
                  <button
                    type="button"
                    class="action-btn action-restore"
                    (click)="abrirModalRestaurar(b)"
                    title="Restaurar backup en la base de datos"
                  >
                    🔄 Restaurar
                  </button>
                  <button
                    type="button"
                    class="action-btn action-delete"
                    (click)="eliminar(b)"
                    title="Eliminar este backup"
                  >
                    🗑
                  </button>
                </div>
              </td>
            </tr>

            <tr *ngIf="backups.length === 0 && !cargando">
              <td colspan="7" class="empty-state">
                <div class="empty-icon">📦</div>
                <p>No se encontraron copias de seguridad registradas.</p>
                <button type="button" class="btn btn-primary" (click)="abrirModalCrear()">
                  Crear el primer backup personalizado ahora
                </button>
              </td>
            </tr>

            <tr *ngIf="cargando">
              <td colspan="7" class="text-center py-4">
                <span class="spinner"></span> Cargando backups...
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ============================================================== -->
      <!-- MODAL: CREAR BACKUP MANUAL PERSONALIZADO                       -->
      <!-- ============================================================== -->
      <div class="modal-backdrop" *ngIf="modalCrearAbierto">
        <div class="modal-card modal-lg">
          <div class="modal-header">
            <h3>Nuevo Backup Personalizado</h3>
            <button type="button" class="close-btn" (click)="modalCrearAbierto = false">✕</button>
          </div>
          <div class="modal-body">
            <div class="form-row">
              <div class="form-group flex-1">
                <label>Nombre del Respaldo (opcional)</label>
                <input
                  type="text"
                  [(ngModel)]="nuevoBackup.nombre"
                  placeholder="Ej: Respaldo_FinDeMes_Inventario"
                />
                <small class="hint">Si se deja vacío, el sistema generará uno automáticamente con marca temporal.</small>
              </div>
              <div class="form-group flex-1">
                <label>Descripción / Notas</label>
                <input
                  type="text"
                  [(ngModel)]="nuevoBackup.descripcion"
                  placeholder="Ej: Previo a balance de temporada alta"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group" *ngIf="isSuperadmin">
                <label>Alcance del Backup</label>
                <select [(ngModel)]="nuevoBackup.alcance">
                  <option value="global">🌐 Todo el Sistema SaaS (Global)</option>
                  <option value="empresa">🏢 Empresa Específica (Tenant)</option>
                </select>
              </div>

              <div class="form-group">
                <label>Formato de Salida</label>
                <select [(ngModel)]="nuevoBackup.formato">
                  <option value="json">JSON Estructurado (Portátil, inspeccionable)</option>
                  <option value="sql">SQL Dump (Transaccional DDL + INSERTs)</option>
                </select>
              </div>

              <div class="form-group">
                <label>Destino de Almacenamiento</label>
                <select [(ngModel)]="nuevoBackup.destino">
                  <option value="ambos">💻 Localhost y ☁️ Nube (Recomendado)</option>
                  <option value="local">💻 Solo Localhost</option>
                  <option value="nube">☁️ Solo Nube (AWS S3)</option>
                </select>
              </div>
            </div>

            <!-- SELECCIÓN PERSONALIZADA DE MÓDULOS -->
            <div class="module-selection-section">
              <div class="section-title-row">
                <h4>Selección Personalizada de Módulos & Tablas:</h4>
                <div class="selection-actions">
                  <button type="button" class="btn-link" (click)="seleccionarTodosModulos(true)">
                    Marcar Todos
                  </button>
                  <span>·</span>
                  <button type="button" class="btn-link" (click)="seleccionarTodosModulos(false)">
                    Desmarcar Todos
                  </button>
                </div>
              </div>

              <div class="modules-grid">
                <div
                  *ngFor="let mod of modulosDisponibles"
                  class="module-card"
                  [class.module-card-checked]="isModuloSeleccionado(mod.id)"
                  (click)="toggleModulo(mod.id)"
                >
                  <div class="mod-check">
                    <input
                      type="checkbox"
                      [checked]="isModuloSeleccionado(mod.id)"
                      (click)="$event.stopPropagation()"
                      (change)="toggleModulo(mod.id)"
                    />
                  </div>
                  <div class="mod-content">
                    <strong>{{ mod.nombre }}</strong>
                    <p>{{ mod.descripcion }}</p>
                    <div class="mod-tables">
                      <span *ngFor="let t of mod.tablas" class="table-tag">{{ t }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-outline" (click)="modalCrearAbierto = false">
              Cancelar
            </button>
            <button
              type="button"
              class="btn btn-primary"
              [disabled]="guardando || modulosSeleccionados.length === 0"
              (click)="confirmarCrearBackup()"
            >
              {{ guardando ? 'Generando Backup...' : '🚀 Generar Backup Ahora' }}
            </button>
          </div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- MODAL: CONFIGURACIÓN DE BACKUP AUTOMÁTICO                      -->
      <!-- ============================================================== -->
      <div class="modal-backdrop" *ngIf="modalConfigAbierto">
        <div class="modal-card">
          <div class="modal-header">
            <h3>Configuración de Backup Automático</h3>
            <button type="button" class="close-btn" (click)="modalConfigAbierto = false">✕</button>
          </div>
          <div class="modal-body" *ngIf="config">
            <div class="toggle-row">
              <div>
                <strong>Habilitar Backup Automático Programado</strong>
                <p class="hint">El sistema ejecutará automáticamente la copia de seguridad según el intervalo configurado.</p>
              </div>
              <label class="switch">
                <input type="checkbox" [(ngModel)]="config.activo" />
                <span class="slider round"></span>
              </label>
            </div>

            <!-- PROGRAMACIÓN DE FECHA Y HORA -->
            <div class="schedule-section">
              <h4 class="schedule-title">📅 Programación de Fecha y Hora del Respaldo:</h4>

              <div class="form-row">
                <div class="form-group flex-1">
                  <label>Tipo de Frecuencia / Programación</label>
                  <select [(ngModel)]="config.frecuencia">
                    <option value="diario">🗓️ Diario (a una hora fija)</option>
                    <option value="semanal">📅 Semanal (un día de la semana)</option>
                    <option value="mensual">📆 Mensual (un día del mes)</option>
                    <option value="fecha_especifica">🎯 Fecha y Hora Específica (Puntual)</option>
                    <option value="cada_hora">⏱️ Cada 1 hora</option>
                    <option value="cada_2_horas">⏱️ Cada 2 horas</option>
                    <option value="cada_4_horas">⏱️ Cada 4 horas</option>
                    <option value="cada_6_horas">⏱️ Cada 6 horas</option>
                    <option value="cada_12_horas">⏱️ Cada 12 horas</option>
                  </select>
                </div>

                <!-- FECHA ESPECÍFICA (CUANDO SE ELIGE PUNTUAL) -->
                <div class="form-group flex-1" *ngIf="config.frecuencia === 'fecha_especifica'">
                  <label>Fecha de Ejecución</label>
                  <input type="date" [(ngModel)]="config.fecha_especifica" />
                  <small class="hint">Día exacto en que se generará el respaldo</small>
                </div>

                <!-- FECHA DE INICIO (PARA PROGRAMACIONES RECURRENTES) -->
                <div class="form-group flex-1" *ngIf="config.frecuencia !== 'fecha_especifica'">
                  <label>Fecha de Inicio (Opcional)</label>
                  <input type="date" [(ngModel)]="config.fecha_inicio" />
                  <small class="hint">A partir de qué día comenzará a correr la tarea</small>
                </div>
              </div>

              <div class="form-row">
                <!-- HORA DE EJECUCIÓN -->
                <div class="form-group flex-1" *ngIf="config.frecuencia === 'diario' || config.frecuencia === 'semanal' || config.frecuencia === 'mensual' || config.frecuencia === 'fecha_especifica'">
                  <label>Hora de Ejecución (HH:MM)</label>
                  <input type="time" [(ngModel)]="config.hora_ejecucion" />
                  <small class="hint">Hora exacta del respaldo (ej. 02:30 AM)</small>
                </div>

                <!-- DÍA DE LA SEMANA (SEMANAL) -->
                <div class="form-group flex-1" *ngIf="config.frecuencia === 'semanal'">
                  <label>Día de la Semana</label>
                  <select [(ngModel)]="config.dia_semana">
                    <option [ngValue]="0">Lunes</option>
                    <option [ngValue]="1">Martes</option>
                    <option [ngValue]="2">Miércoles</option>
                    <option [ngValue]="3">Jueves</option>
                    <option [ngValue]="4">Viernes</option>
                    <option [ngValue]="5">Sábado</option>
                    <option [ngValue]="6">Domingo</option>
                  </select>
                </div>

                <!-- DÍA DEL MES (MENSUAL) -->
                <div class="form-group flex-1" *ngIf="config.frecuencia === 'mensual'">
                  <label>Día del Mes (1 al 28)</label>
                  <input type="number" [(ngModel)]="config.dia_mes" min="1" max="28" />
                  <small class="hint">Día de cada mes para ejecutar el backup</small>
                </div>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group flex-1">
                <label>Destino de Almacenamiento</label>
                <select [(ngModel)]="config.destino">
                  <option value="ambos">Ambos (Localhost y Nube AWS S3)</option>
                  <option value="local">Solo Localhost</option>
                  <option value="nube">Solo Nube (AWS S3)</option>
                </select>
              </div>

              <div class="form-group flex-1">
                <label>Formato de Salida</label>
                <select [(ngModel)]="config.formato">
                  <option value="json">JSON</option>
                  <option value="sql">SQL</option>
                </select>
              </div>

              <div class="form-group flex-1">
                <label>Retención de Copias</label>
                <input type="number" [(ngModel)]="config.retencion_dias" min="1" max="365" />
                <small class="hint">Días a conservar</small>
              </div>
            </div>

            <div class="info-banner" *ngIf="config.proxima_ejecucion">
              <span>📅 Próxima ejecución estimada: <strong>{{ config.proxima_ejecucion | date:'medium' }}</strong></span>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-outline" (click)="modalConfigAbierto = false">
              Cancelar
            </button>
            <button
              type="button"
              class="btn btn-primary"
              [disabled]="guardandoConfig"
              (click)="guardarConfiguracion()"
            >
              {{ guardandoConfig ? 'Guardando...' : 'Guardar Configuración' }}
            </button>
          </div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- MODAL: DETALLE / INSPECCIÓN                                    -->
      <!-- ============================================================== -->
      <div class="modal-backdrop" *ngIf="modalDetalleAbierto && backupSeleccionado">
        <div class="modal-card modal-lg">
          <div class="modal-header">
            <h3>Detalle del Backup: {{ backupSeleccionado.nombre }}</h3>
            <button type="button" class="close-btn" (click)="modalDetalleAbierto = false">✕</button>
          </div>
          <div class="modal-body">
            <div class="detail-grid">
              <div><strong>ID:</strong> <code>{{ backupSeleccionado.id }}</code></div>
              <div><strong>Tipo:</strong> {{ backupSeleccionado.tipo | uppercase }}</div>
              <div><strong>Alcance:</strong> {{ backupSeleccionado.alcance | uppercase }}</div>
              <div><strong>Formato:</strong> {{ backupSeleccionado.formato | uppercase }}</div>
              <div><strong>Tamaño:</strong> {{ backupSeleccionado.tamano_legible }} ({{ backupSeleccionado.tamano_bytes }} bytes)</div>
              <div><strong>Registros Totales:</strong> {{ backupSeleccionado.total_registros }}</div>
              <div><strong>Localhost:</strong> {{ backupSeleccionado.guardado_local ? '✓ ' + backupSeleccionado.ruta_local : 'No almacenado localmente' }}</div>
              <div><strong>Nube:</strong> {{ backupSeleccionado.guardado_nube ? '✓ ' + backupSeleccionado.url_nube : 'No subido a la nube' }}</div>
              <div class="checksum-row">
                <strong>Checksum SHA-256:</strong>
                <code>{{ backupSeleccionado.checksum_sha256 }}</code>
              </div>
            </div>

            <h4 class="mt-4">Desglose de Tablas y Registros:</h4>
            <div class="tables-summary-grid">
              <div *ngFor="let item of getDetallesTablas(backupSeleccionado)" class="table-stat-pill">
                <span class="t-name">{{ item.tabla }}</span>
                <span class="t-count">{{ item.count }} filas</span>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" (click)="modalDetalleAbierto = false">
              Cerrar
            </button>
          </div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- MODAL: RESTAURAR BACKUP                                        -->
      <!-- ============================================================== -->
      <div class="modal-backdrop" *ngIf="modalRestaurarAbierto && backupSeleccionado">
        <div class="modal-card">
          <div class="modal-header">
            <h3>Restaurar Copia de Seguridad</h3>
            <button type="button" class="close-btn" (click)="modalRestaurarAbierto = false">✕</button>
          </div>
          <div class="modal-body">
            <div class="warning-banner">
              ⚠️ <strong>Atención:</strong> Esta acción reinsertará los registros respaldados en la base de datos utilizando inserción transaccional segura (ON CONFLICT DO NOTHING para evitar sobreescritura de claves únicas duplicadas).
            </div>

            <p class="mt-3">
              ¿Desea restaurar los datos del backup <strong>{{ backupSeleccionado.nombre }}</strong> ({{ backupSeleccionado.total_registros }} registros)?
            </p>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-outline" (click)="modalRestaurarAbierto = false">
              Cancelar
            </button>
            <button
              type="button"
              class="btn btn-danger"
              [disabled]="restaurando"
              (click)="confirmarRestaurar()"
            >
              {{ restaurando ? 'Restaurando...' : 'Confirmar Restauración' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .backups-page {
      padding: 24px;
      max-width: 1400px;
      margin: 0 auto;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      color: #1e293b;
    }

    .header-container {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 16px;
    }

    h2 {
      margin: 0 0 6px 0;
      font-size: 1.6rem;
      font-weight: 700;
      color: #0f172a;
    }

    .subtitle {
      margin: 0;
      color: #64748b;
      font-size: 0.95rem;
    }

    .role-pill {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 4px;
    }

    .role-badge {
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
    }

    .badge-super {
      background: #ede9fe;
      color: #6d28d9;
      border: 1px solid #c4b5fd;
    }

    .badge-admin {
      background: #e0f2fe;
      color: #0369a1;
      border: 1px solid #7dd3fc;
    }

    .tenant-name code {
      background: #f1f5f9;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 0.8rem;
    }

    /* ALERTAS */
    .alert-box {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 18px;
      border-radius: 8px;
      margin-bottom: 20px;
      font-size: 0.92rem;
    }

    .alert-success { background: #dcfce7; color: #166534; border: 1px solid #86efac; }
    .alert-danger { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
    .alert-info { background: #e0f2fe; color: #075985; border: 1px solid #7dd3fc; }
    .alert-close { background: none; border: none; font-size: 1.1rem; cursor: pointer; color: inherit; }

    /* STATS GRID */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }

    .stat-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 18px;
      display: flex;
      align-items: center;
      gap: 16px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
      transition: transform 0.15s ease, box-shadow 0.15s ease;
    }

    .stat-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }

    .stat-icon {
      font-size: 2rem;
      width: 52px;
      height: 52px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .icon-backups { background: #f1f5f9; }
    .icon-local { background: #ecfdf5; }
    .icon-cloud { background: #eff6ff; }
    .icon-auto { background: #faf5ff; }

    .stat-info {
      display: flex;
      flex-direction: column;
    }

    .stat-title {
      font-size: 0.8rem;
      color: #64748b;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .stat-number {
      font-size: 1.5rem;
      font-weight: 700;
      color: #0f172a;
      line-height: 1.2;
      margin: 4px 0 2px 0;
    }

    .stat-meta {
      font-size: 0.78rem;
      color: #64748b;
    }

    .stat-badge {
      display: inline-block;
      width: fit-content;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 0.75rem;
      font-weight: 700;
      margin: 4px 0 2px 0;
    }

    .badge-on { background: #dcfce7; color: #166534; }
    .badge-off { background: #f1f5f9; color: #64748b; }

    /* ACTION BAR */
    .action-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      margin-bottom: 20px;
    }

    .action-buttons {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }

    .btn {
      padding: 8px 16px;
      border-radius: 6px;
      font-size: 0.88rem;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: all 0.15s ease;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    .btn-primary { background: #2563eb; color: #ffffff; }
    .btn-primary:hover { background: #1d4ed8; }

    .btn-secondary { background: #f8fafc; color: #334155; border: 1px solid #cbd5e1; }
    .btn-secondary:hover { background: #f1f5f9; }

    .btn-outline { background: transparent; color: #475569; border: 1px solid #cbd5e1; }
    .btn-outline:hover { background: #f8fafc; }

    .btn-danger { background: #dc2626; color: #ffffff; }
    .btn-danger:hover { background: #b91c1c; }

    .filter-controls {
      display: flex;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
    }

    .filter-chips {
      display: flex;
      gap: 6px;
    }

    .chip {
      padding: 6px 12px;
      border-radius: 20px;
      border: 1px solid #e2e8f0;
      background: #ffffff;
      font-size: 0.8rem;
      font-weight: 500;
      color: #475569;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .chip:hover {
      background: #f8fafc;
      border-color: #cbd5e1;
    }

    .chip-active {
      background: #0f172a;
      color: #ffffff;
      border-color: #0f172a;
    }

    .search-box input {
      padding: 7px 12px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      font-size: 0.85rem;
      width: 180px;
      outline: none;
    }

    .search-box input:focus {
      border-color: #2563eb;
      box-shadow: 0 0 0 2px rgba(37,99,235,0.15);
    }

    /* TABLE */
    .table-container {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      overflow-x: auto;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    .data-table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.88rem;
    }

    .data-table th, .data-table td {
      padding: 12px 16px;
      border-bottom: 1px solid #f1f5f9;
      vertical-align: middle;
    }

    .data-table th {
      background: #f8fafc;
      color: #475569;
      font-weight: 600;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .backup-title {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .format-badge {
      font-size: 0.7rem;
      padding: 2px 5px;
      border-radius: 4px;
      font-weight: 700;
    }

    .fmt-json { background: #fef3c7; color: #92400e; }
    .fmt-sql { background: #dbeafe; color: #1e40af; }

    .backup-sub {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-top: 4px;
    }

    .scope-tag {
      font-size: 0.72rem;
      padding: 1px 6px;
      border-radius: 4px;
      font-weight: 500;
    }

    .scope-global { background: #ede9fe; color: #5b21b6; }
    .scope-empresa { background: #f1f5f9; color: #334155; }

    .backup-desc {
      color: #64748b;
      font-size: 0.78rem;
    }

    .type-badge {
      font-size: 0.75rem;
      padding: 3px 8px;
      border-radius: 12px;
      font-weight: 600;
    }

    .type-manual { background: #e0f2fe; color: #0369a1; }
    .type-auto { background: #f3e8ff; color: #7e22ce; }

    /* STORAGE BADGES */
    .storage-cell {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .storage-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 6px;
      width: fit-content;
    }

    .badge-local-ok {
      background: #ecfdf5;
      color: #065f46;
      border: 1px solid #a7f3d0;
    }

    .badge-cloud-ok {
      background: #eff6ff;
      color: #1e40af;
      border: 1px solid #bfdbfe;
    }

    .dot-ok { color: #10b981; font-size: 0.8rem; }
    .dot-cloud { color: #3b82f6; font-size: 0.9rem; }

    .cloud-meta {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .cloud-s3-uri {
      color: #64748b;
      font-family: monospace;
      font-size: 0.72rem;
      max-width: 140px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .btn-icon {
      padding: 3px 8px;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 4px;
      font-size: 0.74rem;
      font-weight: 600;
      color: #334155;
      cursor: pointer;
      transition: all 0.15s ease;
      width: fit-content;
    }

    .btn-icon:hover {
      background: #f1f5f9;
      border-color: #94a3b8;
    }

    .btn-cloud-dl {
      color: #2563eb;
      border-color: #93c5fd;
    }

    .btn-cloud-dl:hover {
      background: #eff6ff;
    }

    .btn-sync-action {
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      border: 1px dashed #cbd5e1;
      background: #f8fafc;
      color: #475569;
      transition: all 0.15s ease;
    }

    .btn-sync-action:hover {
      background: #f1f5f9;
      border-color: #94a3b8;
    }

    .btn-sync-cloud {
      color: #2563eb;
      border-color: #bfdbfe;
      background: #eff6ff;
    }

    .action-group {
      display: flex;
      justify-content: flex-end;
      gap: 6px;
    }

    .action-btn {
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 0.78rem;
      border: 1px solid #e2e8f0;
      background: #ffffff;
      cursor: pointer;
      font-weight: 500;
    }

    .action-view:hover { background: #f8fafc; color: #0284c7; }
    .action-restore:hover { background: #ecfdf5; color: #059669; border-color: #a7f3d0; }
    .action-delete:hover { background: #fef2f2; color: #dc2626; border-color: #fecaca; }

    .empty-state {
      text-align: center;
      padding: 40px !important;
      color: #64748b;
    }

    .empty-icon { font-size: 3rem; margin-bottom: 12px; }

    /* MODALES */
    .modal-backdrop {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(15, 23, 42, 0.55);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      padding: 20px;
      backdrop-filter: blur(2px);
    }

    .modal-card {
      background: #ffffff;
      border-radius: 12px;
      width: 100%;
      max-width: 580px;
      max-height: 90vh;
      overflow-y: auto;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.15);
      display: flex;
      flex-direction: column;
    }

    .modal-lg { max-width: 820px; }

    .modal-header {
      padding: 16px 20px;
      border-bottom: 1px solid #e2e8f0;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .modal-header h3 { margin: 0; font-size: 1.2rem; font-weight: 700; color: #0f172a; }
    .close-btn { background: none; border: none; font-size: 1.2rem; cursor: pointer; color: #64748b; }

    .modal-body { padding: 20px; }
    .modal-footer {
      padding: 14px 20px;
      border-top: 1px solid #e2e8f0;
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      background: #f8fafc;
      border-radius: 0 0 12px 12px;
    }

    .form-row {
      display: flex;
      gap: 16px;
      margin-bottom: 14px;
      flex-wrap: wrap;
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .flex-1 { flex: 1; min-width: 180px; }

    .form-group label {
      font-size: 0.82rem;
      font-weight: 600;
      color: #334155;
    }

    .form-group input, .form-group select {
      padding: 8px 12px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      font-size: 0.88rem;
      outline: none;
    }

    .form-group input:focus, .form-group select:focus {
      border-color: #2563eb;
      box-shadow: 0 0 0 2px rgba(37,99,235,0.15);
    }

    .hint { font-size: 0.74rem; color: #64748b; margin-top: 2px; }

    /* MÓDULOS GRID */
    .module-selection-section {
      margin-top: 16px;
      padding-top: 14px;
      border-top: 1px solid #e2e8f0;
    }

    .section-title-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }

    .section-title-row h4 { margin: 0; font-size: 0.95rem; color: #1e293b; }
    .selection-actions { font-size: 0.8rem; display: flex; gap: 6px; align-items: center; }
    .btn-link { background: none; border: none; color: #2563eb; cursor: pointer; padding: 0; font-size: inherit; }

    .modules-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 10px;
      max-height: 280px;
      overflow-y: auto;
      padding-right: 4px;
    }

    .module-card {
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 10px;
      display: flex;
      gap: 10px;
      cursor: pointer;
      transition: all 0.15s ease;
      background: #ffffff;
    }

    .module-card:hover {
      border-color: #94a3b8;
      background: #f8fafc;
    }

    .module-card-checked {
      border-color: #2563eb;
      background: #eff6ff;
    }

    .mod-content strong { font-size: 0.85rem; color: #0f172a; }
    .mod-content p { margin: 2px 0 6px 0; font-size: 0.74rem; color: #64748b; }
    .mod-tables { display: flex; flex-wrap: wrap; gap: 4px; }
    .table-tag { font-size: 0.68rem; background: #f1f5f9; padding: 1px 5px; border-radius: 3px; font-family: monospace; }

    /* SWITCH TOGGLE */
    .toggle-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 14px;
      background: #f8fafc;
      border-radius: 8px;
      margin-bottom: 18px;
      border: 1px solid #e2e8f0;
    }

    .schedule-section {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 14px;
      margin-bottom: 16px;
    }

    .schedule-title {
      margin: 0 0 12px 0;
      font-size: 0.92rem;
      font-weight: 700;
      color: #1e293b;
    }

    .switch {
      position: relative;
      display: inline-block;
      width: 48px;
      height: 26px;
    }

    .switch input { opacity: 0; width: 0; height: 0; }
    .slider {
      position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
      background-color: #cbd5e1; transition: .3s;
    }
    .slider:before {
      position: absolute; content: ""; height: 20px; width: 20px; left: 3px; bottom: 3px;
      background-color: white; transition: .3s;
    }
    input:checked + .slider { background-color: #10b981; }
    input:checked + .slider:before { transform: translateX(22px); }
    .slider.round { border-radius: 26px; }
    .slider.round:before { border-radius: 50%; }

    .info-banner {
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      color: #1e40af;
      padding: 10px 14px;
      border-radius: 6px;
      font-size: 0.85rem;
      margin-top: 14px;
    }

    .warning-banner {
      background: #fffbeb;
      border: 1px solid #fde68a;
      color: #92400e;
      padding: 12px 16px;
      border-radius: 6px;
      font-size: 0.88rem;
    }

    .detail-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      font-size: 0.88rem;
      background: #f8fafc;
      padding: 14px;
      border-radius: 8px;
      border: 1px solid #e2e8f0;
    }

    .checksum-row {
      grid-column: span 2;
      word-break: break-all;
    }

    .tables-summary-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 8px;
      margin-top: 10px;
    }

    .table-stat-pill {
      background: #f1f5f9;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 6px 10px;
      display: flex;
      justify-content: space-between;
      font-size: 0.8rem;
    }

    .t-name { font-weight: 600; font-family: monospace; }
    .t-count { color: #2563eb; font-weight: 600; }

    .text-right { text-align: right; }
    .text-center { text-align: center; }
    .text-muted { color: #64748b; }
    .text-success { color: #166534; }
    .text-primary { color: #1d4ed8; }
    .mt-3 { margin-top: 12px; }
    .mt-4 { margin-top: 16px; }
    .py-4 { padding-top: 16px; padding-bottom: 16px; }
  `]
})
export class BackupsComponent implements OnInit {
  private readonly controller = inject(CU37GestionBackupsController);
  private readonly auth = inject(AuthService);

  user = this.auth.user;
  isSuperadmin = false;

  backups: BackupRegistro[] = [];
  stats: BackupEstadisticas | null = null;
  config: BackupConfiguracion | null = null;
  modulosDisponibles: BackupModuloInfo[] = [];

  // Filtros
  filtroDestino = '';
  filtroTipo = '';
  searchQuery = '';
  cargando = false;
  ejecutandoAuto = false;
  guardando = false;
  guardandoConfig = false;
  restaurando = false;

  // Alertas
  alertMessage: string | null = null;
  alertType: 'success' | 'danger' | 'info' = 'info';

  // Modales
  modalCrearAbierto = false;
  modalConfigAbierto = false;
  modalDetalleAbierto = false;
  modalRestaurarAbierto = false;

  backupSeleccionado: BackupRegistro | null = null;

  // Modelo de creación manual
  nuevoBackup: BackupCreateRequest = {
    nombre: '',
    descripcion: '',
    alcance: 'empresa',
    formato: 'json',
    destino: 'ambos',
    modulos: [],
  };
  modulosSeleccionados: string[] = [];

  ngOnInit(): void {
    const u = this.user();
    this.isSuperadmin = (u?.rol === 'superadmin' && !u?.empresa_id);
    if (this.isSuperadmin) {
      this.nuevoBackup.alcance = 'global';
    } else {
      this.nuevoBackup.alcance = 'empresa';
    }

    this.cargarDatos();
  }

  cargarDatos(): void {
    this.cargando = true;

    this.controller.obtenerEstadisticas().subscribe({
      next: (s) => (this.stats = s),
      error: () => {},
    });

    this.controller.modulosDisponibles().subscribe({
      next: (mods) => {
        this.modulosDisponibles = mods;
        if (this.modulosSeleccionados.length === 0) {
          this.modulosSeleccionados = mods.map((m) => m.id);
        }
      },
      error: () => {},
    });

    this.cargarBackups();
  }

  cargarBackups(): void {
    this.cargando = true;
    this.controller
      .listarBackups({
        destino: this.filtroDestino || undefined,
        tipo: this.filtroTipo || undefined,
        search: this.searchQuery || undefined,
        page_size: 50,
      })
      .subscribe({
        next: (resp) => {
          this.backups = resp.items || [];
          this.cargando = false;
        },
        error: (err) => {
          this.cargando = false;
          this.mostrarAlerta('No se pudieron cargar los backups.', 'danger');
        },
      });
  }

  setFiltro(destino: string, tipo: string): void {
    this.filtroDestino = destino;
    this.filtroTipo = tipo;
    this.cargarBackups();
  }

  onSearchChange(): void {
    this.cargarBackups();
  }

  abrirModalCrear(): void {
    this.nuevoBackup.nombre = '';
    this.nuevoBackup.descripcion = '';
    this.nuevoBackup.destino = 'ambos';
    this.nuevoBackup.formato = 'json';
    this.modulosSeleccionados = this.modulosDisponibles.map((m) => m.id);
    this.modalCrearAbierto = true;
  }

  toggleModulo(modId: string): void {
    const idx = this.modulosSeleccionados.indexOf(modId);
    if (idx >= 0) {
      this.modulosSeleccionados.splice(idx, 1);
    } else {
      this.modulosSeleccionados.push(modId);
    }
  }

  isModuloSeleccionado(modId: string): boolean {
    return this.modulosSeleccionados.includes(modId);
  }

  seleccionarTodosModulos(marcar: boolean): void {
    this.modulosSeleccionados = marcar ? this.modulosDisponibles.map((m) => m.id) : [];
  }

  confirmarCrearBackup(): void {
    this.guardando = true;
    this.nuevoBackup.modulos = this.modulosSeleccionados;

    this.controller.crearBackupManual(this.nuevoBackup).subscribe({
      next: (b) => {
        this.guardando = false;
        this.modalCrearAbierto = false;
        this.mostrarAlerta(`✓ Backup "${b.nombre}" generado y almacenado con éxito.`, 'success');
        this.cargarDatos();
      },
      error: (err) => {
        this.guardando = false;
        this.mostrarAlerta('Error al generar backup: ' + (err.error?.detail?.message || err.message), 'danger');
      },
    });
  }

  abrirModalConfig(): void {
    this.controller.obtenerConfiguracion().subscribe({
      next: (cfg) => {
        this.config = cfg;
        this.modalConfigAbierto = true;
      },
      error: () => {
        this.mostrarAlerta('No se pudo cargar la configuración del backup.', 'danger');
      },
    });
  }

  guardarConfiguracion(): void {
    if (!this.config) return;
    this.guardandoConfig = true;

    this.controller.guardarConfiguracion(this.config).subscribe({
      next: (res) => {
        this.guardandoConfig = false;
        this.modalConfigAbierto = false;
        this.mostrarAlerta('✓ Configuración de backup automático actualizada.', 'success');
        this.cargarDatos();
      },
      error: (err) => {
        this.guardandoConfig = false;
        this.mostrarAlerta('Error al guardar configuración: ' + (err.error?.detail?.message || err.message), 'danger');
      },
    });
  }

  ejecutarAutoAhora(): void {
    this.ejecutandoAuto = true;
    this.controller.ejecutarBackupAuto().subscribe({
      next: (ids) => {
        this.ejecutandoAuto = false;
        this.mostrarAlerta(`✓ Tarea de backup automático ejecutada con éxito (${ids.length} respaldos generados).`, 'success');
        this.cargarDatos();
      },
      error: (err) => {
        this.ejecutandoAuto = false;
        this.mostrarAlerta('Error al ejecutar backup automático: ' + (err.error?.detail?.message || err.message), 'danger');
      },
    });
  }

  descargar(backup: BackupRegistro, location: 'local' | 'cloud'): void {
    this.controller.descargarArchivo(backup.id, location).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${backup.nombre}.${backup.formato}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        this.mostrarAlerta(`✓ Descarga de "${backup.nombre}" iniciada desde ${location === 'cloud' ? 'la Nube (AWS S3)' : 'Localhost'}.`, 'info');
      },
      error: (err) => {
        this.mostrarAlerta('Error al descargar el archivo: ' + err.message, 'danger');
      },
    });
  }

  sincronizarNube(backup: BackupRegistro): void {
    this.controller.sincronizarNube(backup.id).subscribe({
      next: () => {
        this.mostrarAlerta(`✓ Backup "${backup.nombre}" sincronizado exitosamente en la Nube (AWS S3).`, 'success');
        this.cargarDatos();
      },
      error: (err) => {
        this.mostrarAlerta('Error al sincronizar con la nube.', 'danger');
      },
    });
  }

  sincronizarLocal(backup: BackupRegistro): void {
    this.controller.sincronizarLocal(backup.id).subscribe({
      next: () => {
        this.mostrarAlerta(`✓ Backup "${backup.nombre}" descargado y disponible en Localhost.`, 'success');
        this.cargarDatos();
      },
      error: (err) => {
        this.mostrarAlerta('Error al sincronizar a local.', 'danger');
      },
    });
  }

  abrirModalDetalle(backup: BackupRegistro): void {
    this.backupSeleccionado = backup;
    this.modalDetalleAbierto = true;
  }

  getDetallesTablas(backup: BackupRegistro): { tabla: string; count: number }[] {
    if (!backup.detalles_tablas) return [];
    return Object.entries(backup.detalles_tablas).map(([tabla, count]) => ({
      tabla,
      count,
    }));
  }

  abrirModalRestaurar(backup: BackupRegistro): void {
    this.backupSeleccionado = backup;
    this.modalRestaurarAbierto = true;
  }

  confirmarRestaurar(): void {
    if (!this.backupSeleccionado) return;
    this.restaurando = true;

    this.controller.restaurarBackup(this.backupSeleccionado.id).subscribe({
      next: (resp) => {
        this.restaurando = false;
        this.modalRestaurarAbierto = false;
        this.mostrarAlerta(`✓ ${resp.mensaje || 'Restauración completada con éxito.'}`, 'success');
      },
      error: (err) => {
        this.restaurando = false;
        this.mostrarAlerta('Error al restaurar: ' + (err.error?.detail?.message || err.message), 'danger');
      },
    });
  }

  eliminar(backup: BackupRegistro): void {
    if (!confirm(`¿Está seguro de eliminar el backup "${backup.nombre}" tanto de Localhost como de la Nube?`)) {
      return;
    }

    this.controller.eliminarBackup(backup.id).subscribe({
      next: () => {
        this.mostrarAlerta(`✓ Backup "${backup.nombre}" eliminado permanentemente.`, 'info');
        this.cargarDatos();
      },
      error: (err) => {
        this.mostrarAlerta('Error al eliminar backup.', 'danger');
      },
    });
  }

  private mostrarAlerta(msg: string, tipo: 'success' | 'danger' | 'info'): void {
    this.alertMessage = msg;
    this.alertType = tipo;
    setTimeout(() => {
      if (this.alertMessage === msg) {
        this.alertMessage = null;
      }
    }, 6000);
  }
}
