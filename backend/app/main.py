import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    auth,
    carrito,
    catalogo,
    checkout,
    colecciones,
    empleados,
    inventario,
    pagos,
    pos,
    proveedores,
    reservas,
    saas,
    sucursales,
    suscripciones,
    sync,
    users,
    reportes,
    inteligencia,
    vestidor,
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

# Módulos CU-17 a CU-24
app.include_router(inventario.router, prefix=settings.api_prefix)
app.include_router(inventario.prendas_router, prefix=settings.api_prefix)
app.include_router(reservas.router, prefix=settings.api_prefix)
app.include_router(carrito.router, prefix=settings.api_prefix)
app.include_router(checkout.router, prefix=settings.api_prefix)
app.include_router(pagos.router, prefix=settings.api_prefix)
app.include_router(pos.router, prefix=settings.api_prefix)
app.include_router(sync.router, prefix=settings.api_prefix)

# Módulos CU-33 a CU-36
app.include_router(reportes.router, prefix=settings.api_prefix)
app.include_router(inteligencia.router, prefix=settings.api_prefix)
app.include_router(vestidor.router, prefix=settings.api_prefix)


@app.get("/health", tags=["Sistema"])
async def health() -> dict:
    async with get_pool().acquire() as conn:
        await conn.fetchval("SELECT 1")
    return {"status": "ok", "app": settings.app_name}
