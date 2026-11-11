from fastapi import HTTPException
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
        if "DELETE FROM soft_lock" in sql:
            if args and str(args[0]) == "invalid-uuid":
                raise ValueError("invalid input syntax for type uuid")
            if self.fetchrow_results.get("delete_soft_lock") is not None:
                return self.fetchrow_results["delete_soft_lock"]
            return {"id": args[0]} if args else {"id": str(uuid.uuid4())}
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
        if "FROM sucursal" in sql:
            return [
                {
                    "id": uuid.uuid4(),
                    "nombre": "Sucursal Centro",
                    "direccion": "Av. Principal 100",
                    "ciudad": "Santa Cruz",
                    "es_matriz": True,
                }
            ]
        if "FROM soft_lock sl" in sql:
            return [
                {
                    "id": uuid.uuid4(),
                    "sucursal_id": uuid.uuid4(),
                    "sucursal_nombre": "Sucursal Centro",
                    "variante_id": uuid.uuid4(),
                    "sku": "FS-VES-001-NEG-M",
                    "prenda_nombre": "Vestido midi",
                    "talla": "M",
                    "color": "Negro",
                    "dispositivo_id": "DEV-001",
                    "cantidad": 2,
                    "expira_en": datetime.now(timezone.utc) + timedelta(minutes=30),
                    "creado_en": datetime.now(timezone.utc),
                }
            ]
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
    assert len(pkg.sucursales) == 1
    assert pkg.sucursales[0]["nombre"] == "Sucursal Centro"

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


async def test_cu27_listar_y_liberar_soft_locks():
    """CU-27: Listado con TTL restante y liberación manual de bloqueos activos."""
    pool = FakePool()
    service = SyncService(pool)
    empresa_id = str(uuid.uuid4())
    sucursal_id = str(uuid.uuid4())

    locks = await service.listar_soft_locks(empresa_id=empresa_id, sucursal_id=sucursal_id)
    assert len(locks) == 1
    assert locks[0].activo is True
    assert locks[0].ttl_restante_segundos > 0
    assert locks[0].sku == "FS-VES-001-NEG-M"
    assert any("DELETE FROM soft_lock" in sql for sql, _ in pool.conn.executed)

    lock_id = str(uuid.uuid4())
    liberado = await service.liberar_soft_lock(empresa_id=empresa_id, lock_id=lock_id)
    assert liberado["liberado"] is True
    assert liberado["id"] == lock_id

    pool.conn.fetchrow_results["delete_soft_lock"] = False

    class NotFoundConn(FakeConn):
        async def fetchrow(self, sql, *args):
            if "DELETE FROM soft_lock" in sql:
                return None
            return await super().fetchrow(sql, *args)

    pool.conn = NotFoundConn()
    with pytest.raises(HTTPException) as exc_404:
        await service.liberar_soft_lock(empresa_id=empresa_id, lock_id=str(uuid.uuid4()))
    assert exc_404.value.status_code == 404

    with pytest.raises(HTTPException) as exc_400:
        await service.liberar_soft_lock(empresa_id=empresa_id, lock_id="invalid-uuid")
    assert exc_400.value.status_code == 400


async def test_cu26_cu31_cu32_reserva_offline_sync_y_conflicto():
    """CU-26/CU-31/CU-32: Sync reserva offline, expiración futura, ID legacy y conflicto."""
    pool = FakePool()
    service = SyncService(pool)
    empresa_id = str(uuid.uuid4())
    usuario_id = str(uuid.uuid4())
    sucursal_id = str(uuid.uuid4())
    var_id = str(uuid.uuid4())
    op_uuid = str(uuid.uuid4())
    visita_pasada = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()

    lote_ok = SyncBatchRequest(
        operaciones=[
            OperacionSyncItem(
                id=op_uuid,
                tipo="reserva_offline",
                sucursal_id=sucursal_id,
                payload={
                    "items": [{"variante_id": var_id, "cantidad": 2}],
                    "fecha_visita": visita_pasada,
                    "probador": True,
                },
                creada_en=datetime.now(timezone.utc).isoformat(),
                idempotency_key=f"IDEMP-{op_uuid}",
            )
        ]
    )
    res_ok = await service.procesar_lote_sync(empresa_id, usuario_id, lote_ok)
    assert res_ok.confirmados == [op_uuid]
    assert res_ok.conflictos == []

    # Verifica expira_en > created_at aunque fecha_visita haya sido hace 5 horas
    reserva_insert = [
        args for sql, args in pool.conn.executed if "INSERT INTO reserva (" in sql
    ][-1]
    assert reserva_insert[5] > datetime.now(timezone.utc)

    # Stock insuficiente debe generar conflicto sin abortar el lote, incluso con ID legacy no-UUID
    class LowStockConn(FakeConn):
        async def fetchrow(self, sql, *args):
            if "inventario" in sql:
                return {"stock_disponible": 1}
            return await super().fetchrow(sql, *args)

    pool.conn = LowStockConn()
    legacy_id = "res-off-1710000001"
    lote_conf = SyncBatchRequest(
        operaciones=[
            OperacionSyncItem(
                id=legacy_id,
                tipo="reserva_offline",
                sucursal_id=sucursal_id,
                payload={
                    "items": [{"variante_id": var_id, "cantidad": 3}],
                    "fecha_visita": datetime.now(timezone.utc).isoformat(),
                },
                creada_en=datetime.now(timezone.utc).isoformat(),
                idempotency_key=f"IDEMP-{legacy_id}",
            )
        ]
    )
    res_conf = await service.procesar_lote_sync(empresa_id, usuario_id, lote_conf)
    assert res_conf.confirmados == []
    assert len(res_conf.conflictos) == 1
    assert res_conf.conflictos[0].id == legacy_id
    assert res_conf.conflictos[0].causa == "stock_insuficiente"
    # El ID persistido en operacion_pendiente debe haberse normalizado a UUID válido
    op_pend_insert = [
        args for sql, args in pool.conn.executed if "INSERT INTO operacion_pendiente" in sql
    ][-1]
    uuid.UUID(str(op_pend_insert[0]))

    # CU-32: resolver conflicto de reserva_offline con decision='ajustar'
    class ConflictReservaConn(FakeConn):
        async def fetchrow(self, sql, *args):
            if "operacion_pendiente" in sql:
                return {
                    "id": str(uuid.uuid4()),
                    "empresa_id": empresa_id,
                    "sucursal_id": sucursal_id,
                    "usuario_id": usuario_id,
                    "tipo": "reserva_offline",
                    "payload": json.dumps(
                        {
                            "items": [{"variante_id": var_id, "cantidad": 2}],
                            "fecha_visita": datetime.now(timezone.utc).isoformat(),
                            "probador": True,
                        }
                    ),
                    "estado": "conflicto",
                }
            return await super().fetchrow(sql, *args)

    pool.conn = ConflictReservaConn()
    res_res = await service.resolver_conflicto(
        empresa_id=empresa_id,
        usuario_id=str(uuid.uuid4()),
        datos=ResolucionConflictoRequest(
            operacion_id=str(uuid.uuid4()),
            decision="ajustar",
            motivo="Stock regularizado para reserva offline",
        ),
    )
    assert res_res["nuevo_estado"] == "resuelta"
    assert any("INSERT INTO reserva (" in sql for sql, _ in pool.conn.executed)

