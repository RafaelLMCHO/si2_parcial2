export interface User {
  id: string;
  empresa_id: string | null;
  nombre: string;
  correo: string;
  telefono?: string | null;
  email_verificado: boolean;
  estado: string;
  rol: string;
  sucursal_id?: string | null;
  ultimo_acceso?: string | null;
  created_at?: string | null;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  usuario: User;
}

export interface RefreshResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RegisterResponse {
  mensaje: string;
  usuario_id: string;
  empresa_id: string;
  email_verificado: boolean;
  verification_token?: string | null;
}

export interface VerifyEmailResponse {
  mensaje: string;
  usuario_id: string;
  empresa_id: string;
}

export interface ApiError {
  detail?: {
    code?: string;
    message?: string;
  };
}

export type PlanLimites = Record<string, number | null>;

export interface Plan {
  codigo: string;
  nombre: string;
  precio_mensual: number;
  moneda: string;
  limites: PlanLimites;
}

export interface Suscripcion {
  id: string;
  plan: Plan;
  estado: string;
  fecha_inicio: string;
  fecha_fin: string | null;
  renovacion_auto: boolean;
  dias_restantes: number | null;
  por_vencer: boolean;
  limites: PlanLimites;
  uso: Record<string, number>;
  ia_habilitada: boolean;
}

export interface EmpresaResumen {
  id: string;
  nombre: string;
  slug: string;
  nit: string;
  correo: string;
  telefono: string | null;
  direccion: string | null;
  estado: string;
  created_at: string;
  sucursales_activas: number;
  suscripcion: Suscripcion | null;
}

export interface EmpresaListResponse {
  items: EmpresaResumen[];
  total: number;
  page: number;
  page_size: number;
}

export interface EmpresaCreateRequest {
  nombre: string;
  nit: string;
  telefono?: string | null;
  direccion: string;
  correo_admin: string;
  nombre_admin: string;
}

export interface EmpresaCreateResponse {
  mensaje: string;
  empresa_id: string;
  slug: string;
  nombre: string;
  nit: string;
  estado: string;
  admin_usuario_id: string;
  admin_correo: string;
  password_temporal: string;
}

export interface MiSuscripcionResponse {
  empresa_id: string;
  empresa_nombre: string;
  suscripcion: Suscripcion;
}

export interface SuscripcionUpsertRequest {
  plan_codigo: string;
  fecha_inicio: string;
  fecha_fin: string;
  estado: string;
  renovacion_auto: boolean;
}

export interface EstadoEmpresaResponse {
  mensaje: string;
  empresa_id: string;
  estado: string;
  suscripcion_estado: string | null;
}

export interface MetricasSaaS {
  total_tenants: number;
  empresas_activas: number;
  suscripciones_por_vencer: number;
  volumen_transaccional: number;
  moneda: string;
  periodo_inicio: string;
  periodo_fin: string;
}


// ==========================================
// CU-15: PROVEEDORES TEXTILES
// ==========================================
export interface Proveedor {
  id: string;
  empresa_id: string;
  nombre: string;
  nit: string;
  correo?: string | null;
  telefono?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProveedorCreateRequest {
  nombre: string;
  nit: string;
  correo?: string | null;
  telefono?: string | null;
}

export interface ProveedorUpdateRequest {
  nombre?: string;
  nit?: string;
  correo?: string | null;
  telefono?: string | null;
}

export interface ProveedorListResponse {
  total: number;
  items: Proveedor[];
}

// ==========================================
// CU-16: TEMPORADAS Y COLECCIONES
// ==========================================
export interface Temporada {
  id: string;
  empresa_id: string;
  nombre: string;
  fecha_inicio?: string | null;
  fecha_fin?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Coleccion {
  id: string;
  empresa_id: string;
  nombre: string;
  anio?: number | null;
  created_at: string;
  updated_at: string;
}

export interface TemporadasColeccionesResponse {
  temporadas: Temporada[];
  colecciones: Coleccion[];
}

// ==========================================
// CU-11: SUCURSALES (BR-02)
// ==========================================
export interface Sucursal {
  id: string;
  empresa_id: string;
  ciudad_id: number;
  ciudad_nombre?: string | null;
  nombre: string;
  direccion: string;
  telefono?: string | null;
  es_matriz: boolean;
  estado: string;
  created_at: string;
  updated_at: string;
}

export interface SucursalCreateRequest {
  nombre: string;
  ciudad_id: number;
  direccion: string;
  telefono?: string | null;
  es_matriz: boolean;
}

export interface SucursalesListResponse {
  total: number;
  activas: number;
  limite_plan: number;
  items: Sucursal[];
}

// ==========================================
// CU-10: USUARIOS Y ROLES POR EMPRESA (BR-12)
// ==========================================
export interface Empleado {
  id: string;
  empresa_id: string;
  nombre: string;
  correo: string;
  rol_nombre: string;
  sucursal_id?: string | null;
  sucursal_nombre?: string | null;
  telefono?: string | null;
  estado: string;
  ultimo_acceso?: string | null;
  created_at: string;
}

export interface EmpleadoCreateRequest {
  nombre: string;
  correo: string;
  password: string;
  rol: string;
  sucursal_id?: string | null;
  telefono?: string | null;
}

export interface EmpleadoListResponse {
  total: number;
  items: Empleado[];
}

export interface RolDisponible {
  id: string;
  nombre: string;
  descripcion?: string | null;
}

// ==========================================
// CU-12, CU-13, CU-14: CATALOGO Y FILTROS
// ==========================================
export interface Variante {
  id: string;
  prenda_id: string;
  talla_id: number;
  talla_nombre?: string | null;
  color_id: number;
  color_nombre?: string | null;
  color_hex?: string | null;
  sku: string;
  codigo_barras?: string | null;
  precio_venta: number;
  costo: number;
  estado: string;
  created_at: string;
  updated_at: string;
}

export interface Prenda {
  id: string;
  empresa_id: string;
  codigo: string;
  nombre: string;
  descripcion?: string | null;
  marca?: string | null;
  genero: string;
  precio_base: number;
  moneda: string;
  categoria_id: string;
  categoria_nombre?: string | null;
  temporada_id?: string | null;
  temporada_nombre?: string | null;
  coleccion_id?: string | null;
  coleccion_nombre?: string | null;
  proveedor_id?: string | null;
  proveedor_nombre?: string | null;
  imagen_url?: string | null;
  estado: string;
  created_at: string;
  updated_at: string;
  variantes: Variante[];
}

export interface PrendaListResponse {
  total: number;
  version_catalogo: number;
  items: Prenda[];
}

export interface ItemSimple {
  id: number | string;
  nombre: string;
  extra?: string | null;
}

export interface AuxiliaresCatalogoResponse {
  categorias: ItemSimple[];
  colores: ItemSimple[];
  tallas: ItemSimple[];
  temporadas: ItemSimple[];
  colecciones: ItemSimple[];
}
