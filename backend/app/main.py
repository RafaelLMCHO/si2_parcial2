import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    auth,
    catalogo,
    colecciones,
    empleados,
    proveedores,
    saas,
    sucursales,
    suscripciones,
    users,
)
from app.core.config import get_settings
from app.db import close_pool, get_pool, init_pool
from app.middleware.audit import audit_middleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_pool()
    yield
    await close_pool()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.frontend_origin.split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(audit_middleware)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(saas.router, prefix=settings.api_prefix)
app.include_router(suscripciones.router, prefix=settings.api_prefix)
app.include_router(empleados.router, prefix=settings.api_prefix)
app.include_router(sucursales.router, prefix=settings.api_prefix)
app.include_router(catalogo.router, prefix=settings.api_prefix)
app.include_router(proveedores.router, prefix=settings.api_prefix)
app.include_router(colecciones.router, prefix=settings.api_prefix)


@app.get("/health", tags=["Sistema"])
async def health() -> dict:
    async with get_pool().acquire() as conn:
        await conn.fetchval("SELECT 1")
    return {"status": "ok", "app": settings.app_name}
