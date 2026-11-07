import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from asyncpg import Connection
from fastapi import HTTPException, status

from app.schemas.inteligencia import (
    AvatarClienteDto,
    FinalizarSesionArRequest,
    IniciarSesionArRequest,
    IniciarSesionArResponse,
    PrendaArResponse,
)

logger = logging.getLogger(__name__)


async def listar_prendas_ar(
    conn: Connection,
    empresa_id: UUID,
) -> List[PrendaArResponse]:
    """CU-36: Obtiene el catálogo de prendas habilitadas con modelos 3D y texturas para Realidad Aumentada."""
    rows = await conn.fetch(
        """
        SELECT
            pa.id,
            pa.prenda_id,
            p.codigo AS codigo_prenda,
            p.nombre AS nombre_prenda,
            p.marca,
            COALESCE(cat.nombre, 'General') AS categoria,
            pa.modelo_url,
            pa.textura_url,
            pa.puntos_ajuste,
            pa.talla_referencia,
            pa.activo
        FROM prenda_ar pa
        JOIN prenda p ON p.id = pa.prenda_id AND p.empresa_id = pa.empresa_id
        LEFT JOIN categoria cat ON cat.id = p.categoria_id AND cat.empresa_id = pa.empresa_id
        WHERE pa.empresa_id = $1 AND pa.activo = true
        ORDER BY p.nombre ASC
        """,
        empresa_id,
    )

    # Si aún no hay registros específicos, generar modelos dinámicos para las primeras prendas
    if not rows:
        prendas = await conn.fetch(
            """
            SELECT p.id, p.codigo, p.nombre, p.marca, cat.nombre AS categoria
            FROM prenda p
            LEFT JOIN categoria cat ON cat.id = p.categoria_id AND cat.empresa_id = p.empresa_id
            WHERE p.empresa_id = $1
            LIMIT 6
            """,
            empresa_id,
        )
        items = []
        for p in prendas:
            items.append(
                PrendaArResponse(
                    id=uuid4(),
                    prenda_id=p["id"],
                    codigo_prenda=p["codigo"],
                    nombre_prenda=p["nombre"],
                    marca=p["marca"],
                    categoria=p["categoria"],
                    modelo_url="/assets/models/ar/casual_tshirt.glb",
                    textura_url="/assets/textures/ar/cotton_blue.png",
                    puntos_ajuste={
                        "hombro_izq": [-0.25, 0.40, 0],
                        "hombro_der": [0.25, 0.40, 0],
                        "cuello": [0, 0.45, 0],
                        "pecho": [0, 0.25, 0.05],
                        "escala_base": 1.0,
                    },
                    talla_referencia="M",
                    activo=True,
                )
            )
        return items

    return [
        PrendaArResponse(
            id=r["id"],
            prenda_id=r["prenda_id"],
            codigo_prenda=r["codigo_prenda"],
            nombre_prenda=r["nombre_prenda"],
            marca=r["marca"],
            categoria=r["categoria"],
            modelo_url=r["modelo_url"],
            textura_url=r["textura_url"],
            puntos_ajuste=r["puntos_ajuste"] if isinstance(r["puntos_ajuste"], dict) else {},
            talla_referencia=r["talla_referencia"],
            activo=r["activo"],
        )
        for r in rows
    ]


async def obtener_prenda_ar_por_id(
    conn: Connection,
    empresa_id: UUID,
    prenda_id: UUID,
) -> PrendaArResponse:
    """CU-36: Obtiene la configuración 3D/AR de una prenda específica."""
    row = await conn.fetchrow(
        """
        SELECT
            pa.id,
            pa.prenda_id,
            p.codigo AS codigo_prenda,
            p.nombre AS nombre_prenda,
            p.marca,
            COALESCE(cat.nombre, 'General') AS categoria,
            pa.modelo_url,
            pa.textura_url,
            pa.puntos_ajuste,
            pa.talla_referencia,
            pa.activo
        FROM prenda_ar pa
        JOIN prenda p ON p.id = pa.prenda_id AND p.empresa_id = pa.empresa_id
        LEFT JOIN categoria cat ON cat.id = p.categoria_id AND cat.empresa_id = pa.empresa_id
        WHERE pa.empresa_id = $1 AND (pa.prenda_id = $2 OR pa.id = $2)
        """,
        empresa_id,
        prenda_id,
    )
    if not row:
        # Fallback dinámico sobre prenda existente
        p_row = await conn.fetchrow(
            """
            SELECT p.id, p.codigo, p.nombre, p.marca, cat.nombre AS categoria
            FROM prenda p
            LEFT JOIN categoria cat ON cat.id = p.categoria_id AND cat.empresa_id = p.empresa_id
            WHERE p.empresa_id = $1 AND p.id = $2
            """,
            empresa_id,
            prenda_id,
        )
        if not p_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prenda no encontrada en la empresa",
            )
        return PrendaArResponse(
            id=uuid4(),
            prenda_id=p_row["id"],
            codigo_prenda=p_row["codigo"],
            nombre_prenda=p_row["nombre"],
            marca=p_row["marca"],
            categoria=p_row["categoria"],
            modelo_url="/assets/models/ar/casual_tshirt.glb",
            textura_url="/assets/textures/ar/cotton_blue.png",
            puntos_ajuste={
                "hombro_izq": [-0.25, 0.40, 0],
                "hombro_der": [0.25, 0.40, 0],
                "cuello": [0, 0.45, 0],
                "escala_base": 1.0,
            },
            talla_referencia="M",
            activo=True,
        )

    return PrendaArResponse(
        id=row["id"],
        prenda_id=row["prenda_id"],
        codigo_prenda=row["codigo_prenda"],
        nombre_prenda=row["nombre_prenda"],
        marca=row["marca"],
        categoria=row["categoria"],
        modelo_url=row["modelo_url"],
        textura_url=row["textura_url"],
        puntos_ajuste=row["puntos_ajuste"] if isinstance(row["puntos_ajuste"], dict) else {},
        talla_referencia=row["talla_referencia"],
        activo=row["activo"],
    )


async def obtener_o_crear_avatar(
    conn: Connection,
    empresa_id: UUID,
    usuario_id: UUID,
) -> AvatarClienteDto:
    """CU-36: Recupera o inicializa el avatar y medidas del usuario."""
    row = await conn.fetchrow(
        """
        SELECT id, nombre, modelo_url, altura_cm, peso_kg, tono_piel
        FROM avatar_cliente
        WHERE empresa_id = $1 AND usuario_id = $2 AND deleted_at IS NULL
        LIMIT 1
        """,
        empresa_id,
        usuario_id,
    )

    if not row:
        avatar_id = uuid4()
        await conn.execute(
            """
            INSERT INTO avatar_cliente (id, empresa_id, usuario_id, nombre, altura_cm, peso_kg, tono_piel)
            VALUES ($1, $2, $3, 'Mi Avatar Personal', 170.0, 68.0, 'medio')
            """,
            avatar_id,
            empresa_id,
            usuario_id,
        )
        # Medidas iniciales
        medidas_init = {
            "hombro": 42.0,
            "busto": 94.0,
            "cintura": 78.0,
            "cadera": 96.0,
            "largo_manga": 60.0,
        }
        for tipo, val in medidas_init.items():
            await conn.execute(
                """
                INSERT INTO medida_corporal (empresa_id, avatar_id, tipo, valor_cm)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (empresa_id, avatar_id, tipo) DO NOTHING
                """,
                empresa_id,
                avatar_id,
                tipo,
                val,
            )
        return AvatarClienteDto(
            id=avatar_id,
            usuario_id=usuario_id,
            nombre="Mi Avatar Personal",
            altura_cm=170.0,
            peso_kg=68.0,
            tono_piel="medio",
            medidas=medidas_init,
        )

    # Cargar medidas
    m_rows = await conn.fetch(
        "SELECT tipo, valor_cm FROM medida_corporal WHERE empresa_id = $1 AND avatar_id = $2",
        empresa_id,
        row["id"],
    )
    medidas_dict = {m["tipo"]: float(m["valor_cm"]) for m in m_rows}

    return AvatarClienteDto(
        id=row["id"],
        usuario_id=usuario_id,
        nombre=row["nombre"],
        modelo_url=row["modelo_url"],
        altura_cm=float(row["altura_cm"]) if row["altura_cm"] else 170.0,
        peso_kg=float(row["peso_kg"]) if row["peso_kg"] else 68.0,
        tono_piel=row["tono_piel"] or "medio",
        medidas=medidas_dict,
    )


async def iniciar_sesion_prueba(
    conn: Connection,
    empresa_id: UUID,
    usuario_id: UUID,
    payload: IniciarSesionArRequest,
) -> IniciarSesionArResponse:
    """CU-36: Inicia una sesión de prueba virtual en el vestidor."""
    prenda_ar = await obtener_prenda_ar_por_id(conn, empresa_id, payload.prenda_id)
    avatar = await obtener_o_crear_avatar(conn, empresa_id, usuario_id)

    sesion_id = uuid4()
    await conn.execute(
        """
        INSERT INTO sesion_prueba_virtual (
            id, empresa_id, usuario_id, avatar_id, prenda_id, variante_id, estado, iniciada_en
        )
        VALUES ($1, $2, $3, $4, $5, $6, 'iniciada', now())
        """,
        sesion_id,
        empresa_id,
        usuario_id,
        avatar.id,
        prenda_ar.prenda_id,
        payload.variante_id,
    )

    return IniciarSesionArResponse(
        sesion_id=sesion_id,
        prenda_ar=prenda_ar,
        avatar=avatar,
        estado="iniciada",
        iniciada_en=datetime.now(),
    )


async def finalizar_sesion_prueba(
    conn: Connection,
    empresa_id: UUID,
    sesion_id: UUID,
    payload: FinalizarSesionArRequest,
) -> Dict[str, Any]:
    """CU-36: Finaliza o cancela la sesión de vestidor virtual."""
    result = await conn.execute(
        """
        UPDATE sesion_prueba_virtual
        SET estado = $1, resultado_url = $2, finalizada_en = now()
        WHERE id = $3 AND empresa_id = $4
        """,
        payload.estado,
        payload.resultado_url,
        sesion_id,
        empresa_id,
    )
    if result == "UPDATE 0":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión de prueba virtual no encontrada",
        )
    return {"status": "ok", "sesion_id": str(sesion_id), "estado": payload.estado}

