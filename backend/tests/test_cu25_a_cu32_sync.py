import pytest
import uuid
import json
from datetime import datetime, timezone, timedelta
from app.services.sync_service import SyncService
from app.schemas.sync import (
    SoftLockCreate,
    NotaCambioCreate,
    SyncBatchRequest,
    OperacionSyncItem,
    ResolucionConflictoRequest
)

pytestmark = pytest.mark.asyncio

class FakeConn:
    def __init__(self):
        self.executed = []
        self.fetchval_results = {}
        self.fetchrow_results = {}
        self.fetch_results = {}

    async def execute(self, sql, *args):
        self.executed.append((sql, args))
        return "OK"

    async def fetchval(self, sql, *args):
        self.executed.append((sql, args))
        return str(uuid.uuid4())

    async def fetchrow(self, sql, *args):
        self.executed.append((sql, args))
        if "inventario" in sql:
            return {"stock_disponible": 10, "bloqueado": 0}
        if "sync_registro_idempotencia" in sql:
            return None
        if "operacion_pendiente" in sql:
            return {
                "id": str(uuid.uuid4()),
                "empresa_id": str(uuid.uuid4()),
                "sucursal_id": str(uuid.uuid4()),
                "tipo": "venta_offline",
                "payload": json.dumps({"lineas": [{"variante_id": str(uuid.uuid4()), "cantidad": 1, "precio_unitario": 50.0}], "total": 50.0}),
                "estado": "conflicto"
            }
        return {"id": str(uuid.uuid4())}

    async def fetch(self, sql, *args):
        self.executed.append((sql, args))
        if "prenda" in sql:
            return [{"id": uuid.uuid4(), "codigo": "PR-01", "nombre": "Camisa Oxford", "precio_base": 120.0, "categoria_id": uuid.uuid4()}]
        if "variante_prenda" in sql:
            return [{"id": uuid.uuid4(), "prenda_id": uuid.uuid4(), "sku": "OX-M", "precio_venta": 120.0, "talla": "M", "color": "Azul"}]
        if "inventario" in sql:
            return [{"variante_id": uuid.uuid4(), "sucursal_id": uuid.uuid4(), "stock_disponible": 10, "stock_minimo": 2}]
        if "operacion_pendiente" in sql:
            return [{
                "id": str(uuid.uuid4()),
                "empresa_id": str(uuid.uuid4()),
                "sucursal_id": str(uuid.uuid4()),
                "sucursal_nombre": "Sucursal Centro",
                "tipo": "venta_offline",
                "payload": {"total": 100},
                "estado": "conflicto",
                "ultimo_error": "Stock insuficiente",
                "creada_en": datetime.now(timezone.utc)
            }]
        return []

    def transaction(self):
        class TxContext:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc, tb):
                pass
        return TxContext()

class FakePool:
    def __init__(self):
        self.conn = FakeConn()

    def acquire(self):
        class ConnContext:
            def __init__(self, c):
                self.c = c
            async def __aenter__(self):
                return self.c
            async def __aexit__(self, exc_type, exc, tb):
                pass
        return ConnContext(self.conn)

async def test_cu25_descargar_catalogo_offline():
    pool = FakePool()
    service = SyncService(pool)
    pkg = await service.descargar_catalogo_offline(empresa_id=str(uuid.uuid4()))
    assert pkg.total_articulos >= 0
    assert len(pkg.prendas) >= 0

async def test_cu27_crear_soft_lock():
    pool = FakePool()
    service = SyncService(pool)
    empresa_id = str(uuid.uuid4())
    lock = await service.crear_soft_lock(
        empresa_id=empresa_id,
        datos=SoftLockCreate(
            sucursal_id=str(uuid.uuid4()),
            variante_id=str(uuid.uuid4()),
            cantidad=2,
            dispositivo_id="DEV-001",
            ttl_minutos=45
        )
    )
    assert lock.cantidad == 2
    assert lock.activo is True

async def test_cu29_qr_hmac_y_nota_cambio():
    pool = FakePool()
    service = SyncService(pool)
    payload = {
        "uuid": str(uuid.uuid4()),
        "fecha_hora_local": datetime.now(timezone.utc).isoformat(),
        "total": 150.0,
        "usuario_id": str(uuid.uuid4())
    }
    firma = service.generar_firma_qr_ticket(payload)
    payload["firma"] = firma
    valid = await service.validar_qr_comprobante(str(uuid.uuid4()), json.dumps(payload))
    assert valid["valido"] is True

    # Nota de cambio
    nota = await service.procesar_nota_cambio(
        empresa_id=str(uuid.uuid4()),
        usuario_id=str(uuid.uuid4()),
        datos=NotaCambioCreate(
            sucursal_id=str(uuid.uuid4()),
            variante_devuelta_id=str(uuid.uuid4()),
            variante_nueva_id=str(uuid.uuid4()),
            cantidad=1,
            motivo="Talla no adecuada",
            qr_firma=firma
        )
    )
    assert nota["estado"] == "confirmada"

async def test_cu31_lote_sync_idempotente():
    pool = FakePool()
    service = SyncService(pool)
    op_id = str(uuid.uuid4())
    lote = SyncBatchRequest(
        operaciones=[
            OperacionSyncItem(
                id=op_id,
                tipo="venta_offline",
                sucursal_id=str(uuid.uuid4()),
                payload={
                    "total": 100.0,
                    "lineas": [{"variante_id": str(uuid.uuid4()), "cantidad": 1, "precio_unitario": 100.0}]
                },
                creada_en=datetime.now(timezone.utc).isoformat(),
                idempotency_key=f"IDEMP-{op_id}"
            )
        ]
    )
    res = await service.procesar_lote_sync(str(uuid.uuid4()), str(uuid.uuid4()), lote)
    assert len(res.confirmados) == 1

async def test_cu32_resolver_conflicto():
    pool = FakePool()
    service = SyncService(pool)
    empresa_id = str(uuid.uuid4())
    conflictos = await service.listar_conflictos(empresa_id)
    assert isinstance(conflictos, list)

    res = await service.resolver_conflicto(
        empresa_id=empresa_id,
        usuario_id=str(uuid.uuid4()),
        datos=ResolucionConflictoRequest(
            operacion_id=str(uuid.uuid4()),
            decision="ajustar",
            motivo="Stock ingresado manualmente"
        )
    )
    assert res["nuevo_estado"] == "resuelta"

