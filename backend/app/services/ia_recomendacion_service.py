import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import httpx
from asyncpg import Connection

from app.core.config import get_settings
from app.core.errors import api_error
from app.db import admin_connection
from app.schemas.recomendacion_ia import (
    OutfitRecomendadoResponse,
    RecomendacionPrendaOut,
)

logger = logging.getLogger(__name__)


def _clasificar_rol_prenda(nombre: str, categoria: str) -> str:
    texto = f"{nombre} {categoria}".lower()
    if any(k in texto for k in ["vestido", "mono", "enterizo", "traje"]):
        return "Prenda Principal (Cuerpo Entero)"
    if any(k in texto for k in ["blusa", "camisa", "top", "camiseta", "chaqueta", "blazer", "abrigo", "suéter", "cardigan"]):
        return "Prenda Superior"
    if any(k in texto for k in ["pantalón", "pantalon", "jeans", "jean", "falda", "short", "bermuda", "legging"]):
        return "Prenda Inferior"
    if any(k in texto for k in ["zapato", "zapatilla", "bota", "sandalia", "tacón", "tacon"]):
        return "Calzado"
    return "Accesorio / Complemento"


async def _obtener_catalogo_activo(conn: Connection, empresa_id: UUID, genero: Optional[str] = None) -> List[Dict[str, Any]]:
    query = """
        SELECT p.id, p.nombre, p.descripcion, p.precio_base, p.genero,
               p.imagen_url,
               c.nombre AS categoria_nombre,
               ARRAY_AGG(DISTINCT t.nombre) FILTER (WHERE t.nombre IS NOT NULL) AS tallas,
               ARRAY_AGG(DISTINCT col.nombre) FILTER (WHERE col.nombre IS NOT NULL) AS colores
          FROM prenda p
          LEFT JOIN categoria c ON c.id = p.categoria_id
          LEFT JOIN variante v ON v.prenda_id = p.id AND v.deleted_at IS NULL
          LEFT JOIN talla t ON t.id = v.talla_id
          LEFT JOIN color col ON col.id = v.color_id
         WHERE p.empresa_id = $1
           AND p.estado = 'activa'
           AND p.deleted_at IS NULL
    """
    params: List[Any] = [empresa_id]
    if genero and genero.lower() != "todos":
        query += " AND (p.genero = $2 OR p.genero = 'unisex')"
        params.append(genero.lower())

    query += " GROUP BY p.id, c.nombre ORDER BY p.created_at DESC LIMIT 60;"
    rows = await conn.fetch(query, *params)

    prendas = []
    for r in rows:
        prendas.append({
            "id": r["id"],
            "nombre": r["nombre"],
            "descripcion": r["descripcion"] or "",
            "precio_base": float(r["precio_base"] or 0.0),
            "genero": r["genero"] or "unisex",
            "categoria_nombre": r["categoria_nombre"] or "General",
            "tallas": r["tallas"] or [],
            "colores": r["colores"] or [],
            "imagen_url": r["imagen_url"] or "/assets/placeholder-fashion.jpg",
            "rol": _clasificar_rol_prenda(r["nombre"], r["categoria_nombre"] or ""),
        })
    return prendas


def _determinar_ocasion_y_estilo(prompt: str) -> Tuple[str, str]:
    p = prompt.lower()
    if any(k in p for k in ["boda", "gala", "graduacion", "noche", "elegante", "fiesta"]):
        return "Evento Especial / Fiesta de Gala", "Glamour & Alta Elegancia"
    if any(k in p for k in ["oficina", "trabajo", "reunion", "entrevista", "ejecutivo"]):
        return "Entorno Profesional / Corporativo", "Smart Casual Ejecutivo"
    if any(k in p for k in ["playa", "verano", "fresco", "calor", "piscina"]):
        return "Vacaciones / Clima Cálido", "Summer Fresh & Resort Chic"
    if any(k in p for k in ["coctel", "cena", "romantica", "cita"]):
        return "Cena / Velada Nocturna", "Cocktail Chic Contemporáneo"
    return "Uso Cotidiano / Fin de Semana", "Urban Casual Sofisticado"


def _armar_outfit_heuristico(
    prendas: List[Dict[str, Any]],
    prenda_base: Optional[Dict[str, Any]] = None,
    ocasion: str = "Uso Cotidiano",
    estilo: str = "Urban Casual",
) -> List[Dict[str, Any]]:
    if not prendas:
        return []

    seleccionadas: List[Dict[str, Any]] = []

    if prenda_base:
        seleccionadas.append(prenda_base)

    roles_presentes = {_clasificar_rol_prenda(p["nombre"], p["categoria_nombre"]) for p in seleccionadas}

    # Si ya tiene vestido/cuerpo entero, buscamos chaqueta o accesorio
    tiene_cuerpo_entero = any("Cuerpo Entero" in r for r in roles_presentes)

    if tiene_cuerpo_entero:
        complementos = [
            p for p in prendas
            if p["id"] not in {x["id"] for x in seleccionadas}
            and ("Calzado" in p["rol"] or "Accesorio" in p["rol"] or "Superior" in p["rol"])
        ]
        if complementos:
            seleccionadas.extend(complementos[:2])
    else:
        # Buscar superior e inferior
        if not any("Superior" in r for r in roles_presentes):
            superiores = [p for p in prendas if "Superior" in p["rol"] and p["id"] not in {x["id"] for x in seleccionadas}]
            if superiores:
                seleccionadas.append(superiores[0])
                roles_presentes.add("Superior")

        if not any("Inferior" in r for r in roles_presentes):
            inferiores = [p for p in prendas if "Inferior" in p["rol"] and p["id"] not in {x["id"] for x in seleccionadas}]
            if inferiores:
                seleccionadas.append(inferiores[0])
                roles_presentes.add("Inferior")

        # Complementar con calzado o accesorio si existe
        otros = [
            p for p in prendas
            if p["id"] not in {x["id"] for x in seleccionadas}
        ]
        if otros and len(seleccionadas) < 3:
            seleccionadas.append(otros[0])

    # Si aún no tenemos suficientes, rellenar con las mejores prendas disponibles
    if len(seleccionadas) < 2 and len(prendas) >= 2:
        for p in prendas:
            if p["id"] not in {x["id"] for x in seleccionadas}:
                seleccionadas.append(p)
            if len(seleccionadas) >= 3:
                break

    return seleccionadas


async def recomendar_por_prompt(
    empresa_id: UUID,
    prompt: str,
    genero: Optional[str] = None,
) -> OutfitRecomendadoResponse:
    async with admin_connection() as conn:
        catalogo = await _obtener_catalogo_activo(conn, empresa_id, genero=genero)

    if not catalogo:
        raise api_error(404, "CATALOGO_VACIO", "No hay prendas activas en el catálogo de esta empresa para generar recomendaciones.")

    ocasion, estilo = _determinar_ocasion_y_estilo(prompt)
    prendas_seleccionadas = _armar_outfit_heuristico(catalogo, ocasion=ocasion, estilo=estilo)

    # Intentar enriquecer con LLM si está configurado
    settings = get_settings()
    llm_key = os.environ.get("LLM_API_KEY") or settings.llm_api_key or ""
    motor = "heuristic-fashion-matrix"
    consejo_stylist = (
        f"Hemos curado esta propuesta bajo el concepto '{estilo}' ideal para {ocasion}. "
        "Las prendas seleccionadas equilibran volumen y textura, combinando tonos armónicos y versatilidad. "
        "Recomendamos calzado en tonos neutros y accesorios metálicos sutiles para elevar el porte general."
    )
    titulo_outfit = f"Look {estilo.split('&')[0].strip()} • Selección Especial"

    if llm_key:
        try:
            prompt_llm = f"""
            Actúa como un Personal Stylist y Director Creativo de Moda de alta costura.
            El cliente busca: "{prompt}".
            Ocasión detectada: {ocasion}.
            Estilo: {estilo}.
            Prendas seleccionadas del catálogo real:
            {json.dumps([{'nombre': p['nombre'], 'categoria': p['categoria_nombre'], 'precio': p['precio_base']} for p in prendas_seleccionadas])}

            Genera un JSON EXACTO con las claves:
            {{
                "titulo_outfit": "Un título editorial atractivo (ej. 'Elegancia Crepuscular Urbana')",
                "consejo_estilista": "2 a 3 oraciones de asesoramiento de moda explicando por qué combinan y cómo lucirlas con actitud."
            }}
            """
            api_url = os.environ.get("LLM_API_URL") or settings.llm_api_url or "https://api.openai.com/v1/chat/completions"
            model = os.environ.get("LLM_MODEL") or settings.llm_model or "gpt-4o-mini"

            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.post(
                    api_url,
                    headers={"Authorization": f"Bearer {llm_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "temperature": 0.3,
                        "response_format": {"type": "json_object"},
                        "messages": [{"role": "user", "content": prompt_llm}],
                    },
                )
                if res.status_code == 200:
                    data = res.json()["choices"][0]["message"]["content"]
                    parsed = json.loads(data)
                    titulo_outfit = parsed.get("titulo_outfit", titulo_outfit)
                    consejo_stylist = parsed.get("consejo_estilista", consejo_stylist)
                    motor = "gemini-gpt-stylist-advisor"
        except Exception as e:
            logger.warning("Fallo llamada LLM recomendaciones (usando fallback heurístico): %s", e)

    # Construir respuesta estructurada
    out_prendas: List[RecomendacionPrendaOut] = []
    precio_total = 0.0

    scores = [98, 95, 93, 90]
    razones = [
        "Pieza angular del outfit: aporta estructura visual y define la paleta principal.",
        "Complemento armónico de textura: balancea el corte y equilibra proporciones.",
        "Toque de contraste moderno que acentúa la silueta y realza la ocasión.",
        "Accesorio de remate perfecto para sellar la propuesta de estilo.",
    ]

    for idx, p in enumerate(prendas_seleccionadas):
        precio_total += p["precio_base"]
        out_prendas.append(
            RecomendacionPrendaOut(
                id=p["id"],
                nombre=p["nombre"],
                descripcion=p["descripcion"],
                precio_base=p["precio_base"],
                categoria_nombre=p["categoria_nombre"],
                genero=p["genero"],
                imagen_url=p["imagen_url"],
                tallas_disponibles=p["tallas"],
                colores_disponibles=p["colores"],
                rol_en_outfit=p["rol"],
                score_afinidad=scores[idx % len(scores)],
                por_que_combina=razones[idx % len(razones)],
            )
        )

    # Prompt para probador virtual Decart Lucy CU-36
    prendas_nombres = ", ".join(p.nombre for p in out_prendas)
    vestidor_prompt = (
        f"A professional high-fashion boutique model wearing a cohesive {estilo.lower()} ensemble comprising "
        f"{prendas_nombres}. Clean luxury studio backdrop, sharp daylight editorial illumination, realistic garment draping and texture."
    )

    return OutfitRecomendadoResponse(
        titulo_outfit=titulo_outfit,
        estilo=estilo,
        ocasion=ocasion,
        consejo_estilista_ia=consejo_stylist,
        score_total=97,
        precio_total=round(precio_total, 2),
        prendas=out_prendas,
        sugerencia_vestidor_prompt=vestidor_prompt,
        motor_utilizado=motor,
    )


async def recomendar_outfit_para_prenda(
    empresa_id: UUID,
    prenda_id: UUID,
    ocasion: Optional[str] = None,
) -> OutfitRecomendadoResponse:
    async with admin_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT p.id, p.nombre, p.descripcion, p.precio_base, p.genero,
                   p.imagen_url,
                   c.nombre AS categoria_nombre
              FROM prenda p
              LEFT JOIN categoria c ON c.id = p.categoria_id
             WHERE p.id = $1 AND p.empresa_id = $2
            """,
            prenda_id,
            empresa_id,
        )
        if not row:
            raise api_error(404, "PRENDA_NO_ENCONTRADA", "La prenda especificada no existe en el catálogo")

        prenda_base = {
            "id": row["id"],
            "nombre": row["nombre"],
            "descripcion": row["descripcion"] or "",
            "precio_base": float(row["precio_base"] or 0.0),
            "genero": row["genero"] or "unisex",
            "categoria_nombre": row["categoria_nombre"] or "General",
            "tallas": [],
            "colores": [],
            "imagen_url": row["imagen_url"] or "/assets/placeholder-fashion.jpg",
            "rol": _clasificar_rol_prenda(row["nombre"], row["categoria_nombre"] or ""),
        }

        catalogo = await _obtener_catalogo_activo(conn, empresa_id, genero=prenda_base["genero"])

    estilo = "Couture Coordination"
    ocasion_texto = ocasion or "Evento Social / Salida Exclusiva"
    prendas_outfit = _armar_outfit_heuristico(catalogo, prenda_base=prenda_base, ocasion=ocasion_texto, estilo=estilo)

    out_prendas: List[RecomendacionPrendaOut] = []
    precio_total = 0.0
    for idx, p in enumerate(prendas_outfit):
        precio_total += p["precio_base"]
        es_base = p["id"] == prenda_base["id"]
        out_prendas.append(
            RecomendacionPrendaOut(
                id=p["id"],
                nombre=p["nombre"],
                descripcion=p["descripcion"],
                precio_base=p["precio_base"],
                categoria_nombre=p["categoria_nombre"],
                genero=p["genero"],
                imagen_url=p["imagen_url"],
                tallas_disponibles=p.get("tallas", []),
                colores_disponibles=p.get("colores", []),
                rol_en_outfit="Prenda Seleccionada (Base)" if es_base else p["rol"],
                score_afinidad=100 if es_base else 95 - (idx * 2),
                por_que_combina=(
                    "Prenda central sobre la que se articula toda la propuesta."
                    if es_base else
                    f"Armoniza de forma natural con {prenda_base['nombre']} aportando equilibrio cromático y elegancia."
                ),
            )
        )

    prendas_nombres = ", ".join(p.nombre for p in out_prendas)
    vestidor_prompt = (
        f"Full fashion editorial look centered around {prenda_base['nombre']} paired with {prendas_nombres}. "
        "Boutique lighting, photorealistic textures and tailored silhouette."
    )

    return OutfitRecomendadoResponse(
        titulo_outfit=f"Look Completo: {prenda_base['nombre']}",
        estilo="Combinación Inteligente",
        ocasion=ocasion_texto,
        consejo_estilista_ia=(
            f"Hemos seleccionado prendas complementarias para lucir {prenda_base['nombre']} con máxima distinción. "
            "Esta combinación juega con la caída del tejido y proporciones estudiadas para estilizar la figura."
        ),
        score_total=98,
        precio_total=round(precio_total, 2),
        prendas=out_prendas,
        sugerencia_vestidor_prompt=vestidor_prompt,
        motor_utilizado="heuristic-fashion-matrix",
    )
