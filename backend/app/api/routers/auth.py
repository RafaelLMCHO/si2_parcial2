from fastapi import APIRouter, Depends, Request

from app.api.deps import CurrentUser, get_current_user
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Autenticacion"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, request: Request) -> LoginResponse:
    return await auth_service.login(
        data,
        ip=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(data: RefreshRequest, request: Request) -> RefreshResponse:
    return await auth_service.refresh(
        data,
        ip=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(data: RegisterRequest, request: Request) -> RegisterResponse:
    return await auth_service.register(data, ip=_client_ip(request))


@router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(data: VerifyEmailRequest, request: Request) -> VerifyEmailResponse:
    return await auth_service.verify_email(data, ip=_client_ip(request))


@router.post("/logout")
async def logout(
    request: Request,
    current: CurrentUser = Depends(get_current_user),
) -> dict:
    return await auth_service.logout(
        empresa_id=current.empresa_id,
        usuario_id=current.user_id,
        session_id=current.session_id,
        ip=_client_ip(request),
    )
