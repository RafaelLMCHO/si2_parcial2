from uuid import UUID
from asyncpg import Connection
from app.services import ml_analytics_service
from app.schemas.inteligencia import (
    DashboardMlResponse,
    DemandaPrediccionResponse,
    SegmentacionClientesResponse,
    SintesisTtsResponse,
)


class CU35DashboardAnaliticoMlController:
    """Controlador Backend para el Caso de Uso CU-35:

    Consultar dashboard analítico ML con síntesis por audio (TTS).
    """

    @staticmethod
    async def consultar_dashboard_ml(
        conn: Connection,
        empresa_id: UUID,
    ) -> DashboardMlResponse:
        return await ml_analytics_service.obtener_dashboard_ml_completo(
            conn, empresa_id
        )

    @staticmethod
    async def predecir_demanda(
        conn: Connection,
        empresa_id: UUID,
    ) -> DemandaPrediccionResponse:
        return await ml_analytics_service.entrenar_y_predecir_demanda(
            conn, empresa_id
        )

    @staticmethod
    async def segmentar_clientes(
        conn: Connection,
        empresa_id: UUID,
    ) -> SegmentacionClientesResponse:
        return await ml_analytics_service.segmentar_clientes_kmeans(
            conn, empresa_id
        )

    @staticmethod
    def generar_audio_sintesis(
        texto: str,
    ) -> SintesisTtsResponse:
        return ml_analytics_service.generar_audio_tts_sintesis(texto)

