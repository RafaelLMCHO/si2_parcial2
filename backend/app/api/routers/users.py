from fastapi import APIRouter, Depends, Request

from app.api.deps import CurrentUser, get_current_user
from app.schemas.auth import UserOut
from app.schemas.user import PasswordChangeRequest, UserUpdateRequest
from app.services import auth_service

router = APIRouter(prefix="/users", tags=["Usuarios"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/me", response_model=UserOut)
async def get_me(current: CurrentUser = Depends(get_current_user)) -> UserOut:
    return await auth_service.get_me(current.empresa_id, current.user_id)


@router.patch("/me", response_model=UserOut)
async def update_me(
    data: UserUpdateRequest,
    request: Request,
    current: CurrentUser = Depends(get_current_user),
) -> UserOut:
    return await auth_service.update_me(
        current.empresa_id,
        current.user_id,
        data,
        ip=_client_ip(request),
    )


@router.post("/me/password")
async def change_password(
    data: PasswordChangeRequest,
    request: Request,
    current: CurrentUser = Depends(get_current_user),
) -> dict:
    return await auth_service.change_password(
        current.empresa_id,
        current.user_id,
        current.session_id,
        data,
        ip=_client_ip(request),
    )
