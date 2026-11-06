from typing import Any, Dict, List
from uuid import UUID
from asyncpg import Connection
from app.services import vestidor_ar_service
from app.schemas.inteligencia import (
    AvatarClienteDto,
    FinalizarSesionArRequest,
    IniciarSesionArRequest,
    IniciarSesionArResponse,
    PrendaArResponse,
)


class CU36VestidorVirtualRaController:
    """Controlador Backend para el Caso de Uso CU-36:

    Utilizar vestidor virtual con Realidad Aumentada (RA).
    """

    @staticmethod
    async def listar_prendas_ar(
        conn: Connection,
        empresa_id: UUID,
    ) -> List[PrendaArResponse]:
        return await vestidor_ar_service.listar_prendas_ar(conn, empresa_id)

    @staticmethod
    async def obtener_prenda_ar(
        conn: Connection,
        empresa_id: UUID,
        prenda_id: UUID,
    ) -> PrendaArResponse:
        return await vestidor_ar_service.obtener_prenda_ar_por_id(
            conn, empresa_id, prenda_id
        )

    @staticmethod
    async def obtener_avatar_usuario(
        conn: Connection,
        empresa_id: UUID,
        usuario_id: UUID,
    ) -> AvatarClienteDto:
        return await vestidor_ar_service.obtener_o_crear_avatar(
            conn, empresa_id, usuario_id
        )

    @staticmethod
    async def iniciar_prueba(
        conn: Connection,
        empresa_id: UUID,
        usuario_id: UUID,
        payload: IniciarSesionArRequest,
    ) -> IniciarSesionArResponse:
        return await vestidor_ar_service.iniciar_sesion_prueba(
            conn, empresa_id, usuario_id, payload
        )

    @staticmethod
    async def finalizar_prueba(
        conn: Connection,
        empresa_id: UUID,
        sesion_id: UUID,
        payload: FinalizarSesionArRequest,
    ) -> Dict[str, Any]:
        return await vestidor_ar_service.finalizar_sesion_prueba(
            conn, empresa_id, sesion_id, payload
        )

