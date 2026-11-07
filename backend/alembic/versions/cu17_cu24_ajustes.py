"""cu17_cu24_ajustes

Revision ID: cu17_cu24_ajustes
Revises: 
Create Date: 2026-11-05 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cu17_cu24_ajustes'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # a) Ampliar CHECK de reserva.estado
    op.execute("ALTER TABLE reserva DROP CONSTRAINT IF EXISTS reserva_estado_check")
    op.execute("ALTER TABLE reserva ALTER COLUMN estado SET DEFAULT 'pendiente_preparacion'")
    op.execute("""
        ALTER TABLE reserva ADD CONSTRAINT reserva_estado_check
        CHECK (estado IN (
            'pendiente_preparacion','preparada','incidencia_stock',
            'activa','confirmada','expirada','cancelada','convertida'
        ))
    """)

    # b) Columnas en reserva
    op.execute("ALTER TABLE reserva ADD COLUMN IF NOT EXISTS codigo varchar(20)")
    op.execute("ALTER TABLE reserva ADD COLUMN IF NOT EXISTS fecha_visita timestamptz")
    op.execute("ALTER TABLE reserva ADD COLUMN IF NOT EXISTS probador varchar(30)")
    op.execute("ALTER TABLE reserva ADD COLUMN IF NOT EXISTS cliente_uuid uuid")
    op.execute("UPDATE reserva SET codigo = 'LEGACY-' || substring(id::text, 1, 6) WHERE codigo IS NULL")
    op.execute("UPDATE reserva SET fecha_visita = created_at WHERE fecha_visita IS NULL")
    op.execute("ALTER TABLE reserva ALTER COLUMN codigo SET NOT NULL")
    op.execute("ALTER TABLE reserva ALTER COLUMN fecha_visita SET NOT NULL")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_reserva_empresa_codigo ON reserva (empresa_id, codigo)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_reserva_empresa_cliente_uuid ON reserva (empresa_id, cliente_uuid) WHERE cliente_uuid IS NOT NULL")

    # c) Ubicacion en inventario
    op.execute("ALTER TABLE inventario ADD COLUMN IF NOT EXISTS ubicacion varchar(60)")

    # d) Ampliar CHECK venta.estado
    op.execute("ALTER TABLE venta DROP CONSTRAINT IF EXISTS venta_estado_check")
    op.execute("""
        ALTER TABLE venta ADD CONSTRAINT venta_estado_check
        CHECK (estado IN (
            'pendiente_pago', 'pagada', 'preparando', 'enviada', 'entregada',
            'completada', 'anulada', 'devuelta', 'pendiente_sync', 'pago_fallido'
        ))
    """)

    # e) Facturacion en venta
    op.execute("ALTER TABLE venta ADD COLUMN IF NOT EXISTS cliente_nombre varchar(120)")
    op.execute("ALTER TABLE venta ADD COLUMN IF NOT EXISTS cliente_documento varchar(30)")

    # f) stripe_evento
    op.execute("""
        CREATE TABLE IF NOT EXISTS stripe_evento (
            id varchar(100) PRIMARY KEY,
            tipo varchar(60) NOT NULL,
            procesado_en timestamptz NOT NULL DEFAULT now()
        )
    """)

    # g) Particiones movimiento_inventario
    op.execute("""
        DO $$
        DECLARE
            d date := DATE '2026-01-01';
        BEGIN
            WHILE d < DATE '2029-01-01' LOOP
                EXECUTE format(
                    'CREATE TABLE IF NOT EXISTS %I PARTITION OF movimiento_inventario FOR VALUES FROM (%L) TO (%L)',
                    'movimiento_inventario_' || to_char(d, 'YYYY_MM'),
                    d,
                    d + interval '1 month'
                );
                d := d + interval '1 month';
            END LOOP;
        END $$;
    """)

    # h) Permisos
    op.execute("""
        INSERT INTO permiso (codigo, descripcion, modulo) VALUES
            ('stock.ajustar', 'Ajustar stock de inventario', 'inventario'),
            ('stock.transferir', 'Transferir stock entre sucursales', 'inventario'),
            ('reservas.crear', 'Crear reservas', 'reservas'),
            ('reservas.ver', 'Consultar reservas', 'reservas'),
            ('reservas.cancelar', 'Cancelar reservas', 'reservas'),
            ('reservas.preparar', 'Preparar reservas en sucursal', 'reservas'),
            ('carrito.gestionar', 'Gestionar carrito de compras', 'carrito'),
            ('pagos.procesar', 'Procesar pagos', 'pagos')
        ON CONFLICT (codigo) DO NOTHING;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS stripe_evento")
    op.execute("ALTER TABLE venta DROP COLUMN IF EXISTS cliente_documento")
    op.execute("ALTER TABLE venta DROP COLUMN IF EXISTS cliente_nombre")
    op.execute("ALTER TABLE inventario DROP COLUMN IF EXISTS ubicacion")
    op.execute("ALTER TABLE reserva DROP COLUMN IF EXISTS cliente_uuid")
    op.execute("ALTER TABLE reserva DROP COLUMN IF EXISTS probador")
    op.execute("ALTER TABLE reserva DROP COLUMN IF EXISTS fecha_visita")
    op.execute("ALTER TABLE reserva DROP COLUMN IF EXISTS codigo")

