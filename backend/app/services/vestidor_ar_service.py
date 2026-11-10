import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import httpx
from asyncpg import Connection
from fastapi import HTTPException, status

from app.core.config import get_settings
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
    """CU-36: Obtiene el catálogo de prendas habilitadas con modelos 3D reales en prenda_ar."""
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

    if not rows:
        return []

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prenda no configurada para Realidad Aumentada en la empresa",
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


# ---------------------------------------------------------------------------
# Integración Oficial Decart Lucy VTON 3.6 (CU-36 Realidad Virtual y Proyección)
# ---------------------------------------------------------------------------

async def obtener_sesion_decart_lucy(
    conn: Connection,
    empresa_id: UUID,
    usuario_id: UUID,
) -> Dict[str, Any]:
    """CU-36: Genera o autoriza la sesión WebRTC / WebSocket de Decart Lucy VTON en tiempo real."""
    settings = get_settings()
    api_key = (os.environ.get("DECART_API_KEY") or settings.decart_api_key or "").strip()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El vestidor virtual Decart Lucy VTON no está disponible: DECART_API_KEY no configurada en el servidor.",
        )

    model = (os.environ.get("DECART_MODEL") or settings.decart_model or "lucy-vton-3.6").strip()
    api_url = (os.environ.get("DECART_API_URL") or settings.decart_api_url or "https://api.decart.ai/v1").rstrip("/")
    stream_url = f"wss://api.decart.ai/v1/stream?model={model}"

    token = api_key
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.post(
                f"{api_url}/realtime/sessions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": model, "ttl_seconds": 900},
            )
            if resp.status_code in (401, 403):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Credenciales DECART_API_KEY rechazadas por el proveedor Decart.",
                )
            if resp.status_code == 200:
                data = resp.json()
                token = data.get("client_token", token)
                stream_url = data.get("webrtc_url", stream_url)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"No se pudo contactar /realtime/sessions de Decart, entregando stream directo: {e}")

    return {
        "motor": "decart-lucy-vton",
        "modelo": model,
        "token": token,
        "stream_url": stream_url,
        "fps": 30,
        "resolucion": "720p",
        "latencia_estimada_ms": 38,
        "estado": "activo",
    }


async def preparar_prompt_lucy_vton(
    conn: Connection,
    empresa_id: UUID,
    prenda_id: UUID,
    color_nombre: Optional[str] = None,
    color_hex: Optional[str] = None,
    talla: Optional[str] = None,
) -> Dict[str, Any]:
    """CU-36: Construye la instrucción y referencia fotográfica para el modelo Decart Lucy VTON."""
    settings = get_settings()
    model = (os.environ.get("DECART_MODEL") or settings.decart_model or "lucy-vton-3.6").strip()

    prenda = await conn.fetchrow(
        """
        SELECT p.nombre, p.descripcion, p.marca,
               COALESCE(
                   (SELECT pr.url FROM prenda_recurso pr
                     WHERE pr.empresa_id = p.empresa_id AND pr.prenda_id = p.id
                     ORDER BY pr.es_principal DESC, pr.orden ASC LIMIT 1),
                   p.imagen_url
               ) AS imagen_url,
               cat.nombre AS categoria
        FROM prenda p
        LEFT JOIN categoria cat ON cat.id = p.categoria_id AND cat.empresa_id = p.empresa_id
        WHERE p.id = $1 AND p.empresa_id = $2
        """,
        prenda_id,
        empresa_id,
    )

    if not prenda:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prenda no encontrada para prueba virtual Lucy VTON",
        )

    nombre = prenda["nombre"]
    marca = f" by {prenda['marca']}" if prenda["marca"] else ""
    color_txt = f" in {color_nombre}" if color_nombre else ""
    talla_txt = f", size {talla}" if talla else ""

    prompt = (
        f"A person wearing a high-end luxury {nombre}{marca}{color_txt}{talla_txt}, "
        f"realistic textile drape, natural fabric creases, exact silhouette body fit, "
        f"photorealistic studio lighting, smooth 30fps integration"
    )

    imagen_url = prenda["imagen_url"]
    if not imagen_url or "cdn.fashionstore.test" in str(imagen_url):
        imagen_url = f"/api/v1/catalogo/prendas/{prenda_id}"

    return {
        "prenda_id": str(prenda_id),
        "prenda_nombre": nombre,
        "prompt": prompt,
        "image_url": imagen_url,
        "color_hex": color_hex or "#1E3A8A",
        "speed": "fast",
        "model": model,
    }


