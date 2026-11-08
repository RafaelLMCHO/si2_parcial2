import os
from generate_class_diagrams import UMLClassDiagram

def generate_clases_cu24(output_dir):
    """CU-24: Gestionar pagos (integración con pasarela Stripe Sandbox)"""
    d = UMLClassDiagram(
        title="CU-24: Gestionar Pagos (Stripe Sandbox Integration)",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - PaymentIntents, webhooks, confirmación y tokenización segura"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Cliente', stereotype='actor',
        attributes=[
            '+ cardHolderName: str',
            '+ clientSecret: str',
            '+ orderId: uuid'
        ],
        methods=[
            '+ enterCardDetails()',
            '+ submitStripePayment()',
            '+ handle3dSecureChallenge()'
        ]
    )
    d.add_class(
        'ui_pay', x=0.21, y_top=0.91, w=0.165,
        name='StripePaymentModal', stereotype='boundary',
        attributes=[
            '- stripeElements: StripeInstance',
            '- cardElement: CardElement',
            '- isProcessing: boolean = false',
            '- errorMessage: string | null'
        ],
        methods=[
            '+ mountStripeElements(): void',
            '+ confirmCardPayment(): Promise<void>',
            '+ displayPaymentError(msg): void'
        ]
    )
    d.add_class(
        'ui_receipt', x=0.21, y_top=0.55, w=0.165,
        name='ConfirmacionPagoComponent', stereotype='boundary',
        attributes=[
            '- transaccionId: string',
            '- montoTotal: number',
            '- estadoPago: string = "succeeded"'
        ],
        methods=[
            '+ renderReceipt(): void',
            '+ downloadInvoicePdf(): void',
            '+ navigateToMyOrders(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU24PagoService', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool',
            '- stripe_secret_key: str',
            '- webhook_endpoint_secret: str'
        ],
        methods=[
            '+ createPaymentIntent(order_id, amount): str',
            '+ handleStripeWebhook(payload, signature): void',
            '+ confirmOrderPayment(intent_id: str): bool',
            '+ logTransactionFailure(err_msg: str): void'
        ]
    )
    d.add_class(
        'pago', x=0.70, y_top=0.91, w=0.22,
        name='PagoTransaccion', stereotype='entity', table='pago_transaccion',
        attributes=[
            '+ id: uuid [PK]',
            '# venta_id: uuid [FK]',
            '+ stripe_intent_id: varchar(80) [UNIQUE]',
            '+ monto: numeric(10,2)',
            '+ estado: varchar(20) = "succeeded"',
            '+ pasarela: varchar(30) = "stripe"',
            '+ creado_en: timestamptz'
        ],
        methods=[
            '+ recordTransaction(data): PagoTransaccion',
            '+ findByIntentId(intent_id): PagoTransaccion'
        ]
    )
    d.add_class(
        'venta', x=0.91, y_top=0.91, w=0.15,
        name='Venta', stereotype='entity', table='venta',
        attributes=[
            '+ id: uuid [PK]',
            '+ total: numeric(10,2)',
            '+ estado: varchar(20) = "pagado"',
            '+ pagado_en: timestamptz'
        ],
        methods=[
            '+ markAsPaid(): void'
        ]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.48, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '# empresa_id: uuid [FK]',
            '+ accion: varchar(20) = "pago_stripe"'
        ],
        methods=[
            '+ logPaymentProcessed(trans_id): void'
        ]
    )
    
    d.add_connector('actor', 'ui_pay', side1='right', side2='left', label="«enters card»")
    d.add_connector('actor', 'ui_receipt', side1='bottom', side2='left', label="«sees voucher»", rad=-0.08)
    d.add_connector('ui_pay', 'ctrl', side1='right', side2='left', label="«confirms payment»", is_dep=True)
    d.add_connector('ctrl', 'pago', side1='right', side2='left', label="«saves transaction»", is_dep=True)
    d.add_connector('ctrl', 'venta', side1='right', side2='left', label="«updates paid status»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_connector('venta', 'pago', side1='left', side2='right', mult1="1", mult2="1..*", is_comp=True)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu24_procesamiento_pagos.png")
    svg_path = os.path.join(output_dir, "clases_cu24_procesamiento_pagos.svg")
    d.save(png_path, svg_path)


def generate_clases_cu25(output_dir):
    """CU-25: Descargar catálogo offline (persistencia en IndexedDB / SQLite)"""
    d = UMLClassDiagram(
        title="CU-25: Descargar Catálogo Offline (Persistencia Local)",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Almacenamiento local particionado para resiliencia offline"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Cliente / Cajero', stereotype='actor',
        attributes=[
            '+ currentTenantSlug: str',
            '+ storageAvailable: bool'
        ],
        methods=[
            '+ triggerCatalogDownload()',
            '+ monitorSyncProgress()',
            '+ switchOfflineMode()'
        ]
    )
    d.add_class(
        'ui_btn', x=0.21, y_top=0.91, w=0.165,
        name='BotonDescargarOfflineComponent', stereotype='boundary',
        attributes=[
            '- isDownloading: boolean = false',
            '- lastDownloadedAt: timestamp | null'
        ],
        methods=[
            '+ onClickDownload(): void',
            '+ showProgressBar(): void'
        ]
    )
    d.add_class(
        'ui_modal', x=0.21, y_top=0.55, w=0.165,
        name='SyncStorageProgressModal', stereotype='boundary',
        attributes=[
            '- progressPercentage: number = 0',
            '- totalItemsCached: number = 0',
            '- isCompleted: boolean = false'
        ],
        methods=[
            '+ updateProgress(pct: number): void',
            '+ displayCompletionToast(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU25OfflineSyncService', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ downloadCatalogBundle(empresa_id): dict',
            '+ persistToIndexedDB(bundle): Promise<void>',
            '+ persistToSQLite(bundle): Promise<void>',
            '+ verifyDataChecksum(bundle): bool'
        ]
    )
    d.add_class(
        'local_db', x=0.43, y_top=0.52, w=0.20,
        name='CatalogoLocalDatabase', stereotype='boundary',
        attributes=[
            '- dbName: str = "fashion_offline"',
            '+ version: int = 1',
            '+ itemsCount: int'
        ],
        methods=[
            '+ bulkInsertProducts(items): void',
            '+ getCachedCatalogVersion(): int'
        ]
    )
    d.add_class(
        'prenda', x=0.70, y_top=0.91, w=0.22,
        name='Prenda', stereotype='entity', table='prenda',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '+ nombre: varchar(120)',
            '+ precio_base: numeric(10,2)',
            '+ estado: varchar(20)'
        ],
        methods=[
            '+ getCatalogBundle(emp_id): list'
        ]
    )
    d.add_class(
        'variante', x=0.91, y_top=0.91, w=0.15,
        name='PrendaVariante', stereotype='entity', table='prenda_variante',
        attributes=[
            '+ id: uuid [PK]',
            '+ sku: varchar(50)',
            '+ talla: varchar(10)',
            '+ color: varchar(40)'
        ],
        methods=[]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.50, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '+ accion: varchar(20) = "descarga_offline"'
        ],
        methods=[
            '+ logOfflineBundleDownloaded(): void'
        ]
    )
    
    d.add_connector('actor', 'ui_btn', side1='right', side2='left', label="«triggers download»")
    d.add_connector('actor', 'ui_modal', side1='bottom', side2='left', label="«watches progress»", rad=-0.08)
    d.add_connector('ui_btn', 'ctrl', side1='right', side2='left', label="«requests bundle»", is_dep=True)
    d.add_connector('ctrl', 'local_db', side1='bottom', side2='top', label="«writes local storage»", is_dep=True)
    d.add_connector('ctrl', 'prenda', side1='right', side2='left', label="«reads catalog»", is_dep=True)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_connector('prenda', 'variante', side1='right', side2='left', mult1="1", mult2="1..*", is_comp=True)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu25_descargar_catalogo_offline.png")
    svg_path = os.path.join(output_dir, "clases_cu25_descargar_catalogo_offline.svg")
    d.save(png_path, svg_path)


def generate_clases_cu26(output_dir):
    """CU-26: Registrar reserva offline (generación de UUID local)"""
    d = UMLClassDiagram(
        title="CU-26: Registrar Reserva Offline (UUID Local)",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Generación descentralizada de UUID v4 y encolamiento local"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Cliente Offline', stereotype='actor',
        attributes=[
            '+ isConnected: bool = False',
            '+ localDeviceId: str'
        ],
        methods=[
            '+ selectPrendasOffline()',
            '+ confirmOfflineBooking()',
            '+ saveOfflineVoucher()'
        ]
    )
    d.add_class(
        'ui_modal', x=0.21, y_top=0.91, w=0.165,
        name='ModalReservaOffline', stereotype='boundary',
        attributes=[
            '- localUuid: string',
            '- selectedItems: ReservaItemDTO[]',
            '- statusBadge: string = "offline_pending"'
        ],
        methods=[
            '+ generateLocalUuid(): string',
            '+ submitOfflineReservation(): Promise<void>',
            '+ queueLocalOperation(): void'
        ]
    )
    d.add_class(
        'ui_voucher', x=0.21, y_top=0.55, w=0.165,
        name='LocalVoucherDisplay', stereotype='boundary',
        attributes=[
            '- localQrCode: string',
            '- syncPendingNotice: string'
        ],
        methods=[
            '+ renderOfflineBarcode(): void',
            '+ showSyncPendingAlert(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU26ReservaOfflineService', stereotype='control',
        attributes=[
            '- storageDriver: SQLite | IndexedDB'
        ],
        methods=[
            '+ createOfflineReservation(data): dict',
            '+ enqueuePendingOperation(op_type, payload): void',
            '+ generateV4Uuid(): str'
        ]
    )
    d.add_class(
        'cola_local', x=0.70, y_top=0.91, w=0.22,
        name='ColaOperacionesLocal', stereotype='entity', table='local_cola_operaciones',
        attributes=[
            '+ local_id: text [PK]',
            '+ tipo: text = "reserva"',
            '+ payload: text',
            '+ estado: text = "pendiente"',
            '+ creado_en: timestamp'
        ],
        methods=[
            '+ enqueue(op: dict): void',
            '+ getPending(): list'
        ]
    )
    d.add_class(
        'reserva_local', x=0.91, y_top=0.91, w=0.15,
        name='ReservaLocal', stereotype='entity', table='local_reserva',
        attributes=[
            '+ id: text [PK]',
            '+ codigo_local: text',
            '+ estado: text'
        ],
        methods=[
            '+ saveLocal(data): void'
        ]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.50, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '+ accion: varchar(20) = "reserva_offline"'
        ],
        methods=[
            '+ logOfflineReservation(): void'
        ]
    )
    
    d.add_connector('actor', 'ui_modal', side1='right', side2='left', label="«submits offline»")
    d.add_connector('actor', 'ui_voucher', side1='bottom', side2='left', label="«stores ticket»", rad=-0.08)
    d.add_connector('ui_modal', 'ctrl', side1='right', side2='left', label="«delegates logic»", is_dep=True)
    d.add_connector('ctrl', 'cola_local', side1='right', side2='left', label="«enqueues operation»", is_dep=True)
    d.add_connector('ctrl', 'reserva_local', side1='right', side2='left', label="«persists local»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_connector('reserva_local', 'cola_local', side1='left', side2='right', mult1="1", mult2="1")
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu26_registrar_reserva_offline.png")
    svg_path = os.path.join(output_dir, "clases_cu26_registrar_reserva_offline.svg")
    d.save(png_path, svg_path)


def generate_clases_cu27(output_dir):
    """CU-27: Bloquear stock local offline con TTL (Soft-Lock temporal)"""
    d = UMLClassDiagram(
        title="CU-27: Bloquear Stock Local Offline con TTL (Soft-Lock)",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Prevención de sobreventas con expiración de tiempo (TTL)"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Cajero / Cron', stereotype='actor',
        attributes=[
            '+ terminalId: str',
            '+ ttlMinutes: int = 15'
        ],
        methods=[
            '+ scanItemForHold()',
            '+ checkHoldTimer()',
            '+ triggerTtlExpiry()'
        ]
    )
    d.add_class(
        'ui_badge', x=0.21, y_top=0.91, w=0.165,
        name='SoftLockStatusBadge', stereotype='boundary',
        attributes=[
            '- lockedSkuCount: number = 0',
            '- remainingTtlSeconds: number',
            '- isExpired: boolean = false'
        ],
        methods=[
            '+ displayLockedQuantity(): void',
            '+ showCountdownTimer(): void'
        ]
    )
    d.add_class(
        'ui_selector', x=0.21, y_top=0.55, w=0.165,
        name='PosItemSelectorComponent', stereotype='boundary',
        attributes=[
            '- selectedSku: string',
            '- requestedQty: number = 1'
        ],
        methods=[
            '+ attemptHold(): Promise<boolean>',
            '+ alertStockUnavailable(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU27SoftLockService', stereotype='control',
        attributes=[
            '- localDb: SQLite | IndexedDB'
        ],
        methods=[
            '+ applyLocalSoftLock(sku, qty, ttl_min): bool',
            '+ releaseExpiredSoftLocks(): int',
            '+ getAvailableUnheldStock(sku): int'
        ]
    )
    d.add_class(
        'softlock', x=0.70, y_top=0.91, w=0.22,
        name='SoftLockLocal', stereotype='entity', table='local_soft_lock',
        attributes=[
            '+ lock_id: text [PK]',
            '+ sku: text',
            '+ cantidad: integer',
            '+ expira_en: timestamp',
            '+ estado: text = "bloqueado"'
        ],
        methods=[
            '+ isExpired(): bool',
            '+ releaseLock(): void'
        ]
    )
    d.add_class(
        'inv_local', x=0.91, y_top=0.91, w=0.15,
        name='InventarioLocal', stereotype='entity', table='local_inventario',
        attributes=[
            '+ sku: text [PK]',
            '+ stock_total: integer',
            '+ stock_retenido: integer'
        ],
        methods=[
            '+ hold(qty): void',
            '+ unhold(qty): void'
        ]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.50, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '+ accion: varchar(20) = "soft_lock_ttl"'
        ],
        methods=[
            '+ logSoftLockApplied(): void'
        ]
    )
    
    d.add_connector('actor', 'ui_badge', side1='right', side2='left', label="«monitors locks»")
    d.add_connector('actor', 'ui_selector', side1='bottom', side2='left', label="«requests hold»", rad=-0.08)
    d.add_connector('ui_selector', 'ctrl', side1='right', side2='left', label="«applies lock»", is_dep=True)
    d.add_connector('ctrl', 'softlock', side1='right', side2='left', label="«creates soft-lock»", is_dep=True)
    d.add_connector('ctrl', 'inv_local', side1='right', side2='left', label="«increments hold»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_connector('inv_local', 'softlock', side1='left', side2='right', mult1="1", mult2="0..*")
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu27_bloquear_stock_soft_lock.png")
    svg_path = os.path.join(output_dir, "clases_cu27_bloquear_stock_soft_lock.svg")
    d.save(png_path, svg_path)


def generate_clases_cu28(output_dir):
    """CU-28: Registrar venta de contado offline (efectivo y ticket preliminar)"""
    d = UMLClassDiagram(
        title="CU-28: Venta de Contado Offline (Efectivo y Ticket)",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Facturación desconectada y mitigación de intermitencia"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Cajero POS', stereotype='actor',
        attributes=[
            '+ offlineTerminalId: str',
            '+ drawerCash: numeric'
        ],
        methods=[
            '+ ringCashSale()',
            '+ receiveCash()',
            '+ issueOfflineTicket()'
        ]
    )
    d.add_class(
        'ui_cash', x=0.21, y_top=0.91, w=0.165,
        name='PosOfflineCashRegister', stereotype='boundary',
        attributes=[
            '- totalCashAmount: number',
            '- cashReceived: number',
            '- changeDue: number = 0'
        ],
        methods=[
            '+ processCashSale(): Promise<void>',
            '+ computeCashChange(): number',
            '+ lockLocalSale(): void'
        ]
    )
    d.add_class(
        'ui_ticket', x=0.21, y_top=0.55, w=0.165,
        name='TicketOfflineThermalView', stereotype='boundary',
        attributes=[
            '- localTicketNumber: string',
            '- timestamp: string',
            '- disclaimer: string = "OFFLINE"'
        ],
        methods=[
            '+ printOfflineTicket(): void',
            '+ stampOfflineWatermark(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU28VentaOfflineController', stereotype='control',
        attributes=[
            '- localDb: SQLite | IndexedDB'
        ],
        methods=[
            '+ recordOfflineCashSale(data): OfflineReceiptDTO',
            '+ decrementLocalInventory(sku, qty): void',
            '+ queueSaleSyncRecord(sale_data): void'
        ]
    )
    d.add_class(
        'venta_local', x=0.70, y_top=0.91, w=0.22,
        name='VentaLocal', stereotype='entity', table='local_venta',
        attributes=[
            '+ local_id: text [PK]',
            '+ cliente: text',
            '+ total: numeric(10,2)',
            '+ estado: text = "pendiente_sync"',
            '+ creado_en: timestamp'
        ],
        methods=[
            '+ insertSale(data): void',
            '+ markSynced(): void'
        ]
    )
    d.add_class(
        'inv_local', x=0.91, y_top=0.91, w=0.15,
        name='InventarioLocal', stereotype='entity', table='local_inventario',
        attributes=[
            '+ sku: text [PK]',
            '+ stock_local: integer'
        ],
        methods=[
            '+ deduct(qty): void'
        ]
    )
    d.add_class(
        'cola_sync', x=0.70, y_top=0.52, w=0.22,
        name='ColaOperacionesLocal', stereotype='entity', table='local_cola_operaciones',
        attributes=[
            '+ id: text [PK]',
            '+ tipo: text = "venta_pos"',
            '+ payload: text'
        ],
        methods=[
            '+ enqueueSync(item): void'
        ]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.24, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '+ accion: varchar(20) = "venta_offline"'
        ],
        methods=[
            '+ logOfflineSale(id): void'
        ]
    )
    
    d.add_connector('actor', 'ui_cash', side1='right', side2='left', label="«charges cash»")
    d.add_connector('actor', 'ui_ticket', side1='bottom', side2='left', label="«prints receipt»", rad=-0.08)
    d.add_connector('ui_cash', 'ctrl', side1='right', side2='left', label="«records offline»", is_dep=True)
    d.add_connector('ctrl', 'venta_local', side1='right', side2='left', label="«stores local sale»", is_dep=True)
    d.add_connector('ctrl', 'inv_local', side1='right', side2='left', label="«deducts stock»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'cola_sync', side1='bottom', side2='top', label="«queues for sync»", is_dep=True)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_connector('venta_local', 'cola_sync', side1='bottom', side2='top', mult1="1", mult2="1")
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu28_venta_contado_offline.png")
    svg_path = os.path.join(output_dir, "clases_cu28_venta_contado_offline.svg")
    d.save(png_path, svg_path)


def generate_clases_cu29(output_dir):
    """CU-29: Validar comprobante y procesar cambio mediante QR offline"""
    d = UMLClassDiagram(
        title="CU-29: Validar Comprobante y Procesar Cambio QR Offline",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Criptografía de comprobante (HMAC), escaneo QR y cambios"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Cajero / Staff', stereotype='actor',
        attributes=[
            '+ terminalId: str',
            '+ deviceKey: str'
        ],
        methods=[
            '+ scanTicketQrCode()',
            '+ verifySignature()',
            '+ selectGarmentExchange()'
        ]
    )
    d.add_class(
        'ui_scan', x=0.21, y_top=0.91, w=0.165,
        name='EscanerQrComprobanteComponent', stereotype='boundary',
        attributes=[
            '- scannedQrPayload: string',
            '- isValidSignature: boolean = false',
            '- ticketDetails: TicketSummaryDTO'
        ],
        methods=[
            '+ activateScanner(): void',
            '+ onQrScanned(raw): void',
            '+ displayTicketSummary(): void'
        ]
    )
    d.add_class(
        'ui_exchange', x=0.21, y_top=0.55, w=0.165,
        name='ModalCambioPrendaOffline', stereotype='boundary',
        attributes=[
            '- returnSku: string',
            '- replacementSku: string',
            '- priceDifference: number = 0'
        ],
        methods=[
            '+ selectReplacementVariant(): void',
            '+ confirmExchange(): Promise<void>',
            '+ printExchangeVoucher(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU29ValidacionQrService', stereotype='control',
        attributes=[
            '- hmac_secret_key: str',
            '- localDb: SQLite'
        ],
        methods=[
            '+ verifyQrSignatureHMAC(qr_payload): TicketDTO',
            '+ validateExchangeEligibility(ticket_date): bool',
            '+ processOfflineExchange(ticket_id, new_sku): dict'
        ]
    )
    d.add_class(
        'ticket_local', x=0.70, y_top=0.91, w=0.22,
        name='TicketComprobanteLocal', stereotype='entity', table='local_ticket_comprobante',
        attributes=[
            '+ hash_comprobante: text [PK]',
            '+ venta_id: text',
            '+ articulos: json',
            '+ hmac_signature: text',
            '+ emitido_en: timestamp'
        ],
        methods=[
            '+ verifySignature(): bool',
            '+ isWithinDaysLimit(days=30): bool'
        ]
    )
    d.add_class(
        'cambio_local', x=0.91, y_top=0.91, w=0.15,
        name='CambioPrendaLocal', stereotype='entity', table='local_cambio_prenda',
        attributes=[
            '+ cambio_id: text [PK]',
            '+ sku_devuelto: text',
            '+ sku_nuevo: text',
            '+ estado: text = "pendiente_sync"'
        ],
        methods=[
            '+ recordExchange(data): void'
        ]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.50, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '+ accion: varchar(20) = "cambio_prenda_qr"'
        ],
        methods=[
            '+ logGarmentExchange(): void'
        ]
    )
    
    d.add_connector('actor', 'ui_scan', side1='right', side2='left', label="«scans QR code»")
    d.add_connector('actor', 'ui_exchange', side1='bottom', side2='left', label="«confirms exchange»", rad=-0.08)
    d.add_connector('ui_scan', 'ctrl', side1='right', side2='left', label="«validates HMAC»", is_dep=True)
    d.add_connector('ui_exchange', 'ctrl', side1='right', side2='bottom', label="«executes swap»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'ticket_local', side1='right', side2='left', label="«verifies payload»", is_dep=True)
    d.add_connector('ctrl', 'cambio_local', side1='right', side2='left', label="«stores exchange»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_connector('ticket_local', 'cambio_local', side1='right', side2='left', mult1="1", mult2="0..*")
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu29_validar_qr_cambio_offline.png")
    svg_path = os.path.join(output_dir, "clases_cu29_validar_qr_cambio_offline.svg")
    d.save(png_path, svg_path)


def generate_clases_cu30(output_dir):
    """CU-30: Consultar cola de operaciones pendientes offline (estados)"""
    d = UMLClassDiagram(
        title="CU-30: Consultar Cola de Operaciones Pendientes Offline",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Monitor de sincronización, auditoría y reintentos"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Encargado / Cajero', stereotype='actor',
        attributes=[
            '+ terminalId: str',
            '+ authorizedRole: str'
        ],
        methods=[
            '+ viewPendingSyncQueue()',
            '+ inspectQueuePayload()',
            '+ triggerManualRetry()'
        ]
    )
    d.add_class(
        'ui_queue', x=0.21, y_top=0.91, w=0.165,
        name='ColaSincronizacionComponent', stereotype='boundary',
        attributes=[
            '- pendingOperations: QueueItemDTO[]',
            '- filterStatus: string = "todas"',
            '- isRetrying: boolean = false'
        ],
        methods=[
            '+ loadQueue(): Promise<void>',
            '+ retryAllFailed(): void',
            '+ openDetailModal(id): void'
        ]
    )
    d.add_class(
        'ui_detail', x=0.21, y_top=0.55, w=0.165,
        name='ModalDetalleOperacion', stereotype='boundary',
        attributes=[
            '- operationId: string',
            '- rawPayloadJson: string',
            '- errorCause: string | null'
        ],
        methods=[
            '+ inspectPayload(): void',
            '+ forceRetrySingle(): void',
            '+ discardOperation(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU30ColaOfflineController', stereotype='control',
        attributes=[
            '- localDb: SQLite | IndexedDB'
        ],
        methods=[
            '+ listPendingOperations(): list',
            '+ retryFailedOperation(op_id): dict',
            '+ clearSyncedOperations(): int'
        ]
    )
    d.add_class(
        'op_local', x=0.70, y_top=0.91, w=0.22,
        name='OperacionPendienteLocal', stereotype='entity', table='local_operacion_pendiente',
        attributes=[
            '+ id: text [PK]',
            '+ tipo: text',
            '+ payload: text',
            '+ reintentos: integer = 0',
            '+ estado: text = "pendiente"',
            '+ ultimo_error: text',
            '+ creado_en: timestamp'
        ],
        methods=[
            '+ markRetrying(): void',
            '+ markSuccess(): void',
            '+ incrementRetryCount(err): void'
        ]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.50, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '+ accion: varchar(20) = "inspeccion_cola_sync"'
        ],
        methods=[
            '+ logQueueInspection(): void'
        ]
    )
    
    d.add_connector('actor', 'ui_queue', side1='right', side2='left', label="«monitors queue»")
    d.add_connector('actor', 'ui_detail', side1='bottom', side2='left', label="«inspects details»", rad=-0.08)
    d.add_connector('ui_queue', 'ctrl', side1='right', side2='left', label="«queries operations»", is_dep=True)
    d.add_connector('ui_detail', 'ctrl', side1='right', side2='bottom', label="«retries operation»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'op_local', side1='right', side2='left', label="«updates status»", is_dep=True)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu30_cola_operaciones_offline.png")
    svg_path = os.path.join(output_dir, "clases_cu30_cola_operaciones_offline.svg")
    d.save(png_path, svg_path)


def generate_clases_cu31(output_dir):
    """CU-31: Sincronizar operaciones pendientes (idempotencia RNF05)"""
    d = UMLClassDiagram(
        title="CU-31: Sincronizar Operaciones Pendientes (Idempotencia)",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Envío por lotes, control de idempotencia y asentado central"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Sistema / Cajero', stereotype='actor',
        attributes=[
            '+ isOnline: bool = True',
            '+ batchSize: int = 50'
        ],
        methods=[
            '+ triggerBatchSync()',
            '+ handleSyncNotification()',
            '+ acknowledgeSyncResult()'
        ]
    )
    d.add_class(
        'ui_sync', x=0.21, y_top=0.91, w=0.165,
        name='BotonSyncComponent', stereotype='boundary',
        attributes=[
            '- isSyncing: boolean = false',
            '- pendingCount: number = 0',
            '- lastSyncAt: timestamp | null'
        ],
        methods=[
            '+ onClickSync(): void',
            '+ showSyncingSpinner(): void',
            '+ renderSyncSuccessBadge(): void'
        ]
    )
    d.add_class(
        'ui_modal', x=0.21, y_top=0.55, w=0.165,
        name='SyncProgressModal', stereotype='boundary',
        attributes=[
            '- progressPercentage: number',
            '- currentBatchIndex: number',
            '- errorsEncountered: number = 0'
        ],
        methods=[
            '+ updateBatchProgress(curr, tot): void',
            '+ renderReportSummary(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU31SyncController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ processSyncBatch(emp_id, batch): dict',
            '+ validateIdempotencyKey(key: str): bool',
            '+ commitOperationToPostgreSQL(op): void'
        ]
    )
    d.add_class(
        'idemp', x=0.70, y_top=0.91, w=0.22,
        name='SyncRegistroIdempotencia', stereotype='entity', table='sync_registro_idempotencia',
        attributes=[
            '+ idempotency_key: text [PK]',
            '# empresa_id: uuid [FK]',
            '+ operacion_tipo: varchar(30)',
            '+ response_hash: text',
            '+ asentado_en: timestamptz'
        ],
        methods=[
            '+ registerKey(key): bool',
            '+ isDuplicate(key): bool'
        ]
    )
    d.add_class(
        'op_backend', x=0.91, y_top=0.91, w=0.15,
        name='OperacionPendiente', stereotype='entity', table='operacion_pendiente',
        attributes=[
            '+ id: uuid [PK]',
            '# sucursal_id: uuid [FK]',
            '+ estado: varchar(20)',
            '+ procesado_en: timestamptz'
        ],
        methods=[
            '+ markAsProcessed(): void'
        ]
    )
    d.add_class(
        'venta', x=0.70, y_top=0.52, w=0.22,
        name='Venta', stereotype='entity', table='venta',
        attributes=[
            '+ id: uuid [PK]',
            '+ numero_factura: varchar(40)',
            '+ total: numeric(10,2)'
        ],
        methods=[
            '+ settleOfflineSale(data): void'
        ]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.24, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '+ accion: varchar(20) = "sincronizar_lote"'
        ],
        methods=[
            '+ logSyncBatchFinished(): void'
        ]
    )
    
    d.add_connector('actor', 'ui_sync', side1='right', side2='left', label="«triggers sync»")
    d.add_connector('actor', 'ui_modal', side1='bottom', side2='left', label="«monitors progress»", rad=-0.08)
    d.add_connector('ui_sync', 'ctrl', side1='right', side2='left', label="«posts batch»", is_dep=True)
    d.add_connector('ctrl', 'idemp', side1='right', side2='left', label="«checks idempotency»", is_dep=True)
    d.add_connector('ctrl', 'op_backend', side1='right', side2='left', label="«updates status»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'venta', side1='right', side2='left', label="«persists sale»", is_dep=True, rad=-0.08)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu31_sincronizar_operaciones.png")
    svg_path = os.path.join(output_dir, "clases_cu31_sincronizar_operaciones.svg")
    d.save(png_path, svg_path)


def generate_clases_cu32(output_dir):
    """CU-32: Resolver conflictos de sincronización con políticas y manual (FIFO)"""
    d = UMLClassDiagram(
        title="CU-32: Resolver Conflictos de Sincronización (FIFO / Manual)",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Resolución determinista de sobreventa y colisiones de inventario"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Encargado / Admin', stereotype='actor',
        attributes=[
            '+ tenantId: uuid',
            '+ resolutionRole: str'
        ],
        methods=[
            '+ inspectConflicts()',
            '+ compareStates()',
            '+ applyFifoPolicy()',
            '+ submitManualOverride()'
        ]
    )
    d.add_class(
        'ui_tray', x=0.21, y_top=0.91, w=0.165,
        name='BandejaConflictosComponent', stereotype='boundary',
        attributes=[
            '- conflictList: ConflictItemDTO[] = []',
            '- selectedConflictId: string | null'
        ],
        methods=[
            '+ loadConflicts(): Promise<void>',
            '+ applyFifoAutomatic(): void',
            '+ openResolveModal(id): void'
        ]
    )
    d.add_class(
        'ui_modal', x=0.21, y_top=0.55, w=0.165,
        name='ModalResolucionConflicto', stereotype='boundary',
        attributes=[
            '- conflictingStockLocal: number',
            '- serverStock: number',
            '- forcedStockAdjustment: number'
        ],
        methods=[
            '+ inspectDiscrepancy(): void',
            '+ submitManualAdjustment(): Promise<void>',
            '+ close(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU32ConflictoSyncController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ listPendingConflicts(empresa_id): list',
            '+ resolveConflictAutomaticFIFO(id): dict',
            '+ resolveConflictManual(id, delta): dict'
        ]
    )
    d.add_class(
        'op', x=0.70, y_top=0.91, w=0.22,
        name='OperacionPendiente', stereotype='entity', table='operacion_pendiente',
        attributes=[
            '+ id: uuid [PK]',
            '+ estado: varchar(20) = "conflicto"',
            '+ error_detalle: text',
            '+ resuelto_en: timestamptz'
        ],
        methods=[
            '+ markResolved(resolution_type): void'
        ]
    )
    d.add_class(
        'inventario', x=0.91, y_top=0.91, w=0.15,
        name='Inventario', stereotype='entity', table='inventario',
        attributes=[
            '+ id: uuid [PK]',
            '+ stock_actual: integer'
        ],
        methods=[
            '+ applyForcedAdjustment(delta): void'
        ]
    )
    d.add_class(
        'movimiento', x=0.70, y_top=0.52, w=0.22,
        name='MovimientoInventario', stereotype='entity', table='movimiento_inventario',
        attributes=[
            '+ id: uuid [PK]',
            '+ tipo: varchar(30) = "ajuste_conflicto_sync"',
            '+ cantidad: integer'
        ],
        methods=[
            '+ recordDiscrepancyMovement(): void'
        ]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.24, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '+ accion: varchar(20) = "resolucion_conflicto"'
        ],
        methods=[
            '+ logConflictResolution(id): void'
        ]
    )
    
    d.add_connector('actor', 'ui_tray', side1='right', side2='left', label="«inspects conflicts»")
    d.add_connector('actor', 'ui_modal', side1='bottom', side2='left', label="«chooses resolution»", rad=-0.08)
    d.add_connector('ui_tray', 'ctrl', side1='right', side2='left', label="«lists conflicts»", is_dep=True)
    d.add_connector('ui_modal', 'ctrl', side1='right', side2='bottom', label="«submits resolution»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'op', side1='right', side2='left', label="«resolves conflict»", is_dep=True)
    d.add_connector('ctrl', 'inventario', side1='right', side2='left', label="«adjusts stock»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'movimiento', side1='right', side2='left', label="«logs kardex»", is_dep=True, rad=-0.08)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu32_resolver_conflictos.png")
    svg_path = os.path.join(output_dir, "clases_cu32_resolver_conflictos.svg")
    d.save(png_path, svg_path)


def generate_clases_cu33(output_dir):
    """CU-33: Reportes y Dashboards Convencionales (Básico y Profesional)"""
    d = UMLClassDiagram(
        title="CU-33: Reportes y Dashboards Convencionales",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Métricas comerciales, rotación de stock y ventas por sucursal"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Administrador', stereotype='actor',
        attributes=[
            '+ tenantId: uuid',
            '+ reportingScope: str'
        ],
        methods=[
            '+ accessDashboard()',
            '+ setFilterCriteria()',
            '+ exportReportPdf()'
        ]
    )
    d.add_class(
        'ui_dash', x=0.21, y_top=0.91, w=0.165,
        name='ReportesConvencionalesComponent', stereotype='boundary',
        attributes=[
            '- kpiSummary: KpiSummaryDTO',
            '- salesChartData: ChartSeries[]',
            '- turnoverTable: TurnoverRow[]'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ renderKpiTiles(): void',
            '+ renderTurnoverChart(): void'
        ]
    )
    d.add_class(
        'ui_filters', x=0.21, y_top=0.55, w=0.165,
        name='FiltrosReporteView', stereotype='boundary',
        attributes=[
            '- dateRangeFrom: string',
            '- dateRangeTo: string',
            '- branchId: string = "todas"'
        ],
        methods=[
            '+ onDateRangeChange(): void',
            '+ onBranchSelect(): void',
            '+ refreshDashboard(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU33ReporteConvencionalController', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool'
        ],
        methods=[
            '+ getConventionalDashboard(emp_id, ini, fin): dict',
            '+ getSalesMetricsByPeriod(emp_id, period): list',
            '+ getStockTurnoverReport(emp_id, suc_id): list'
        ]
    )
    d.add_class(
        'venta', x=0.70, y_top=0.91, w=0.22,
        name='Venta', stereotype='entity', table='venta',
        attributes=[
            '+ id: uuid [PK]',
            '+ total: numeric(10,2)',
            '+ creado_en: timestamptz'
        ],
        methods=[
            '+ aggregateSales(emp_id, range): dict'
        ]
    )
    d.add_class(
        'detalle', x=0.91, y_top=0.91, w=0.15,
        name='VentaDetalle', stereotype='entity', table='venta_detalle',
        attributes=[
            '+ id: uuid [PK]',
            '+ cantidad: integer',
            '+ precio_unitario: numeric'
        ],
        methods=[
            '+ getTopSellingSkus(emp_id): list'
        ]
    )
    d.add_class(
        'inventario', x=0.70, y_top=0.52, w=0.22,
        name='Inventario', stereotype='entity', table='inventario',
        attributes=[
            '+ id: uuid [PK]',
            '+ stock_actual: integer',
            '+ stock_minimo: integer'
        ],
        methods=[
            '+ getCriticalStockList(emp_id): list'
        ]
    )
    d.add_class(
        'movimiento', x=0.91, y_top=0.52, w=0.15,
        name='MovimientoInventario', stereotype='entity', table='movimiento_inventario',
        attributes=[
            '+ id: uuid [PK]',
            '+ tipo: varchar(30)',
            '+ cantidad: integer'
        ],
        methods=[]
    )
    
    d.add_connector('actor', 'ui_dash', side1='right', side2='left', label="«views analytics»")
    d.add_connector('actor', 'ui_filters', side1='bottom', side2='left', label="«sets dates»", rad=-0.08)
    d.add_connector('ui_dash', 'ctrl', side1='right', side2='left', label="«fetches metrics»", is_dep=True)
    d.add_connector('ui_filters', 'ctrl', side1='right', side2='bottom', label="«applies filters»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'venta', side1='right', side2='left', label="«aggregates revenue»", is_dep=True)
    d.add_connector('ctrl', 'inventario', side1='right', side2='left', label="«analyzes turnover»", is_dep=True, rad=-0.08)
    
    d.add_connector('venta', 'detalle', side1='right', side2='left', mult1="1", mult2="1..*", is_comp=True)
    d.add_connector('inventario', 'movimiento', side1='right', side2='left', mult1="1", mult2="0..*")
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu33_reportes_convencionales.png")
    svg_path = os.path.join(output_dir, "clases_cu33_reportes_convencionales.svg")
    d.save(png_path, svg_path)


def generate_clases_cu34(output_dir):
    """CU-34: Solicitar reporte generativo IA y exportar PDF/Excel (Whitelist BR-08)"""
    d = UMLClassDiagram(
        title="CU-34: Reportes Generativos con IA (Whitelist)",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Consultas en lenguaje natural, whitelist SQL y exportación XLSX/PDF"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Gerente (Pro)', stereotype='actor',
        attributes=[
            '+ tenantPlan: str = "pro"',
            '+ voiceSupported: bool'
        ],
        methods=[
            '+ dictateAiPrompt()',
            '+ typeAiQuestion()',
            '+ previewAiInsights()',
            '+ exportSpreadsheet()'
        ]
    )
    d.add_class(
        'ui_ai', x=0.21, y_top=0.91, w=0.165,
        name='ReporteIaComponent', stereotype='boundary',
        attributes=[
            '- promptInput: string = ""',
            '- isListening: boolean = false',
            '- generatedInsights: AiInsightCard[]'
        ],
        methods=[
            '+ sendPrompt(): Promise<void>',
            '+ startVoiceRecognition(): void',
            '+ renderInsightCards(): void'
        ]
    )
    d.add_class(
        'ui_export', x=0.21, y_top=0.55, w=0.165,
        name='ModalExportarDocumento', stereotype='boundary',
        attributes=[
            '- selectedFormat: string = "xlsx"',
            '- isExporting: boolean = false'
        ],
        methods=[
            '+ selectFormat(fmt): void',
            '+ downloadDocument(): Promise<void>'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU34IaReporteService', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool',
            '- llm_client: GeminiAPIClient',
            '- whitelist_tables: set'
        ],
        methods=[
            '+ processNaturalLanguageQuery(prompt, emp_id): dict',
            '+ validateSqlWhitelistBR08(sql: str): bool',
            '+ exportReportDocument(data, fmt): bytes'
        ]
    )
    d.add_class(
        'log_ia', x=0.70, y_top=0.91, w=0.22,
        name='ConsultaIaLog', stereotype='entity', table='consulta_ia_log',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '# usuario_id: uuid [FK]',
            '+ prompt_original: text',
            '+ tokens_consumidos: integer',
            '+ sql_ejecutado: text',
            '+ duracion_ms: integer'
        ],
        methods=[
            '+ logQuery(data): void'
        ]
    )
    d.add_class(
        'export', x=0.91, y_top=0.91, w=0.15,
        name='ReporteExportado', stereotype='entity', table='reporte_exportado',
        attributes=[
            '+ id: uuid [PK]',
            '+ formato: varchar(10)',
            '+ url_archivo: text',
            '+ bytes_tamano: integer'
        ],
        methods=[
            '+ recordExport(data): void'
        ]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.50, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '+ accion: varchar(20) = "consulta_ia_generativa"'
        ],
        methods=[
            '+ logAiQueryExecuted(): void'
        ]
    )
    
    d.add_connector('actor', 'ui_ai', side1='right', side2='left', label="«prompts in NL»")
    d.add_connector('actor', 'ui_export', side1='bottom', side2='left', label="«exports document»", rad=-0.08)
    d.add_connector('ui_ai', 'ctrl', side1='right', side2='left', label="«processes prompt»", is_dep=True)
    d.add_connector('ui_export', 'ctrl', side1='right', side2='bottom', label="«requests export»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'log_ia', side1='right', side2='left', label="«records AI usage»", is_dep=True)
    d.add_connector('ctrl', 'export', side1='right', side2='left', label="«generates file»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu34_reporte_generativo_ia.png")
    svg_path = os.path.join(output_dir, "clases_cu34_reporte_generativo_ia.svg")
    d.save(png_path, svg_path)


def generate_clases_cu35(output_dir):
    """CU-35: Consultar dashboard analítico ML con síntesis por audio (TTS)"""
    d = UMLClassDiagram(
        title="CU-35: Dashboard Analítico ML con Síntesis TTS",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Predicción de demanda (Random Forest), segmentación (K-Means) y voz"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Director / Gerente', stereotype='actor',
        attributes=[
            '+ tenantId: uuid',
            '+ audioEnabled: bool = True'
        ],
        methods=[
            '+ inspectDemandForecast()',
            '+ examineCustomerClusters()',
            '+ playAudioSummary()'
        ]
    )
    d.add_class(
        'ui_ml', x=0.21, y_top=0.91, w=0.165,
        name='DashboardMlComponent', stereotype='boundary',
        attributes=[
            '- forecastSeries: DemandPointDTO[]',
            '- clusterScatter: ClusterPointDTO[]',
            '- modelMetrics: ModelAccuracyDTO'
        ],
        methods=[
            '+ ngOnInit(): void',
            '+ renderForecastChart(): void',
            '+ renderClusterPlot(): void'
        ]
    )
    d.add_class(
        'ui_tts', x=0.21, y_top=0.55, w=0.165,
        name='ReproductorAudioTtsView', stereotype='boundary',
        attributes=[
            '- audioUrl: string | null',
            '- isPlaying: boolean = false',
            '- audioProgress: number = 0'
        ],
        methods=[
            '+ playVoiceBriefing(): void',
            '+ pauseAudio(): void',
            '+ seekTime(position): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU35MlAnalyticsService', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool',
            '- tts_engine: TextToSpeechClient'
        ],
        methods=[
            '+ trainAndPredictDemand(empresa_id): dict',
            '+ segmentCustomersKMeans(empresa_id, k=4): dict',
            '+ generateTtsSpeechSynthesis(text): bytes'
        ]
    )
    d.add_class(
        'modelo_ml', x=0.70, y_top=0.91, w=0.22,
        name='ModeloMl', stereotype='entity', table='modelo_ml',
        attributes=[
            '+ id: uuid [PK]',
            '# empresa_id: uuid [FK]',
            '+ tipo_modelo: varchar(40)',
            '+ r2_score: numeric(5,4)',
            '+ silhouette_score: numeric(5,4)',
            '+ parametros: jsonb'
        ],
        methods=[
            '+ saveModelMetrics(data): void',
            '+ getLatestModel(tipo): ModeloMl'
        ]
    )
    d.add_class(
        'cliente', x=0.91, y_top=0.91, w=0.15,
        name='Cliente', stereotype='entity', table='cliente',
        attributes=[
            '+ id: uuid [PK]',
            '+ total_gastado: numeric(10,2)',
            '+ recencia_dias: integer'
        ],
        methods=[
            '+ getRfmMatrix(emp_id): list'
        ]
    )
    d.add_class(
        'venta', x=0.70, y_top=0.50, w=0.22,
        name='Venta', stereotype='entity', table='venta',
        attributes=[
            '+ id: uuid [PK]',
            '+ total: numeric(10,2)',
            '+ creado_en: timestamptz'
        ],
        methods=[
            '+ getDailyTimeSeries(emp_id): list'
        ]
    )
    d.add_class(
        'audit', x=0.70, y_top=0.24, w=0.22,
        name='BitacoraAuditoria', stereotype='entity', table='bitacora_auditoria',
        attributes=[
            '+ id: bigserial [PK]',
            '+ accion: varchar(20) = "ejecucion_modelo_ml"'
        ],
        methods=[
            '+ logModelExecution(): void'
        ]
    )
    
    d.add_connector('actor', 'ui_ml', side1='right', side2='left', label="«inspects ML KPIs»")
    d.add_connector('actor', 'ui_tts', side1='bottom', side2='left', label="«listens briefing»", rad=-0.08)
    d.add_connector('ui_ml', 'ctrl', side1='right', side2='left', label="«runs models»", is_dep=True)
    d.add_connector('ui_tts', 'ctrl', side1='right', side2='bottom', label="«generates speech»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'modelo_ml', side1='right', side2='left', label="«stores scores»", is_dep=True)
    d.add_connector('ctrl', 'cliente', side1='right', side2='left', label="«clusters clients»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'venta', side1='right', side2='left', label="«trains regressor»", is_dep=True, rad=-0.08)
    d.add_connector('ctrl', 'audit', side1='bottom', side2='left', label="«audits»", is_dep=True, rad=-0.12)
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu35_dashboard_analitico_ml.png")
    svg_path = os.path.join(output_dir, "clases_cu35_dashboard_analitico_ml.svg")
    d.save(png_path, svg_path)


def generate_clases_cu36(output_dir):
    """CU-36: Utilizar vestidor virtual con Realidad Aumentada (RA)"""
    d = UMLClassDiagram(
        title="CU-36: Vestidor Virtual con Realidad Aumentada (RA)",
        subtitle="Diagrama de Clases de Diseño (ICONIX) - Modelos 3D (.glb), tracking corporal y sesión de prueba virtual"
    )
    d.add_class(
        'actor', x=0.065, y_top=0.88, w=0.105,
        name='Cliente Web/Móvil', stereotype='actor',
        attributes=[
            '+ customerId: uuid',
            '+ cameraGranted: bool'
        ],
        methods=[
            '+ selectArGarment()',
            '+ grantCameraAccess()',
            '+ captureVirtualSnapshot()'
        ]
    )
    d.add_class(
        'ui_ar', x=0.21, y_top=0.91, w=0.165,
        name='VestidorVirtualComponent', stereotype='boundary',
        attributes=[
            '- activeModel3dUrl: string',
            '- selectedColor: string',
            '- isTrackingActive: boolean = false'
        ],
        methods=[
            '+ load3dCatalog(): void',
            '+ selectSizeColor(): void',
            '+ onSnapshotCapture(): void'
        ]
    )
    d.add_class(
        'ui_cam', x=0.21, y_top=0.55, w=0.165,
        name='CamaraArCanvasView', stereotype='boundary',
        attributes=[
            '- videoElement: HTMLVideoElement',
            '- arCanvas: HTMLCanvasElement',
            '- trackedJointsCount: number'
        ],
        methods=[
            '+ startCameraStream(): Promise<void>',
            '+ renderArOverlay3d(): void',
            '+ trackBodyJoints(): void'
        ]
    )
    d.add_class(
        'ctrl', x=0.43, y_top=0.91, w=0.22,
        name='CU36VestidorArService', stereotype='control',
        attributes=[
            '- pool: asyncpg.Pool',
            '- model3dStorageUrl: str'
        ],
        methods=[
            '+ listArGarments(empresa_id): list',
            '+ getOrCreateAvatar(cli_id, body_data): dict',
            '+ startVirtualFittingSession(cli_id, prenda_id): dict',
            '+ endVirtualFittingSession(ses_id, snap): str'
        ]
    )
    d.add_class(
        'prenda_ar', x=0.70, y_top=0.91, w=0.22,
        name='PrendaAr', stereotype='entity', table='prenda_ar',
        attributes=[
            '+ id: uuid [PK]',
            '# prenda_id: uuid [FK]',
            '+ modelo_3d_url: text',
            '+ escala_factor: numeric(5,2)',
            '+ anclajes_hombro: jsonb',
            '+ formato_archivo: varchar(10) = "glb"'
        ],
        methods=[
            '+ getActiveArModels(emp_id): list'
        ]
    )
    d.add_class(
        'avatar', x=0.91, y_top=0.91, w=0.15,
        name='AvatarCliente', stereotype='entity', table='avatar_cliente',
        attributes=[
            '+ id: uuid [PK]',
            '# cliente_id: uuid [FK]',
            '+ altura_cm: numeric(5,2)',
            '+ peso_kg: numeric(5,2)',
            '+ tono_piel: varchar(30)'
        ],
        methods=[
            '+ getProfileMeasurements(): dict'
        ]
    )
    d.add_class(
        'sesion_ar', x=0.70, y_top=0.50, w=0.22,
        name='SesionPruebaVirtual', stereotype='entity', table='sesion_prueba_virtual',
        attributes=[
            '+ id: uuid [PK]',
            '# cliente_id: uuid [FK]',
            '# prenda_ar_id: uuid [FK]',
            '+ duracion_segundos: integer',
            '+ snapshot_url: text',
            '+ creado_en: timestamptz'
        ],
        methods=[
            '+ recordFittingSession(data): void'
        ]
    )
    d.add_class(
        'medida', x=0.91, y_top=0.50, w=0.15,
        name='MedidaCorporal', stereotype='entity', table='medida_corporal',
        attributes=[
            '+ id: uuid [PK]',
            '# avatar_id: uuid [FK]',
            '+ busto_cm: numeric(5,2)',
            '+ cintura_cm: numeric(5,2)',
            '+ cadera_cm: numeric(5,2)'
        ],
        methods=[]
    )
    
    d.add_connector('actor', 'ui_ar', side1='right', side2='left', label="«selects 3D piece»")
    d.add_connector('actor', 'ui_cam', side1='bottom', side2='left', label="«stands in AR camera»", rad=-0.08)
    d.add_connector('ui_ar', 'ctrl', side1='right', side2='left', label="«loads 3D asset»", is_dep=True)
    d.add_connector('ui_cam', 'ctrl', side1='right', side2='bottom', label="«starts session»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'prenda_ar', side1='right', side2='left', label="«fetches .glb»", is_dep=True)
    d.add_connector('ctrl', 'avatar', side1='right', side2='left', label="«scales by avatar»", is_dep=True, rad=0.08)
    d.add_connector('ctrl', 'sesion_ar', side1='bottom', side2='top', label="«records session»", is_dep=True)
    
    d.add_connector('avatar', 'medida', side1='bottom', side2='top', mult1="1", mult2="1", is_comp=True)
    d.add_connector('prenda_ar', 'sesion_ar', side1='bottom', side2='top', mult1="1", mult2="0..*")
    
    d.add_legend()
    png_path = os.path.join(output_dir, "clases_cu36_vestidor_virtual_ra.png")
    svg_path = os.path.join(output_dir, "clases_cu36_vestidor_virtual_ra.svg")
    d.save(png_path, svg_path)

