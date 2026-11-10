from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, get_conn, require_permission
from app.schemas.inteligencia import (
    DashboardMlResponse,
    DemandaPrediccionResponse,
    SegmentacionClientesResponse,
    SintesisTtsRequest,
    SintesisTtsResponse,
)
from app.services import ml_analytics_service

router = APIRouter(prefix="/inteligencia", tags=["Machine Learning e IA"])


# ---------------------------------------------------------------------------
# CU-35: Dashboard Analítico de Machine Learning & TTS
# ---------------------------------------------------------------------------

@router.get("/ml/dashboard", response_model=DashboardMlResponse)
async def get_dashboard_ml_completo(
    demo: bool = Query(False, description="Usar dataset demo si no hay histórico suficiente"),
    user: CurrentUser = Depends(require_permission("reportes:leer")),
    conn=Depends(get_conn),
):
    """CU-35: Consulta el tablero analítico ML con predicción de demanda, segmentación y audio TTS."""
    return await ml_analytics_service.obtener_dashboard_ml_completo(
        conn, user.empresa_id, demo=demo
    )


@router.get("/ml/demanda", response_model=DemandaPrediccionResponse)
async def get_prediccion_demanda_supervisada(
    demo: bool = Query(False, description="Usar dataset demo si no hay histórico suficiente"),
    user: CurrentUser = Depends(require_permission("reportes:leer")),
    conn=Depends(get_conn),
):
    """CU-35: Modelo supervisado scikit-learn para proyección de demanda futura."""
    return await ml_analytics_service.entrenar_y_predecir_demanda(
        conn, user.empresa_id, demo=demo
    )


@router.get("/ml/segmentacion", response_model=SegmentacionClientesResponse)
async def get_segmentacion_clientes_kmeans(
    demo: bool = Query(False, description="Usar dataset demo si no hay clientes suficientes"),
    user: CurrentUser = Depends(require_permission("reportes:leer")),
    conn=Depends(get_conn),
):
    """CU-35: Modelo no supervisado scikit-learn K-Means para segmentación RFM."""
    return await ml_analytics_service.segmentar_clientes_kmeans(
        conn, user.empresa_id, demo=demo
    )


@router.post("/ml/sintesis-audio", response_model=SintesisTtsResponse)
async def generar_audio_sintesis(
    payload: SintesisTtsRequest,
    user: CurrentUser = Depends(require_permission("reportes:leer")),
):
    """CU-35: Genera audio WAV sintético para la narración ejecutiva de los resultados."""
    return ml_analytics_service.generar_audio_tts_sintesis(payload.texto)

