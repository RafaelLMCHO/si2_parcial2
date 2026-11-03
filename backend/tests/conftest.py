import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db import close_pool, init_pool
from app.main import app


@pytest_asyncio.fixture
async def client():
    await init_pool()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    await close_pool()


async def login(client: AsyncClient, correo: str, password: str, empresa_slug: str | None = "demo"):
    payload = {"correo": correo, "password": password}
    if empresa_slug is not None:
        payload["empresa_slug"] = empresa_slug
    return await client.post("/api/v1/auth/login", json=payload)
