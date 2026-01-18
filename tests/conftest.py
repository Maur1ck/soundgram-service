import pytest_asyncio
import httpx
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest_asyncio.fixture
async def http_client():
    """Простой клиент для тестов сервисов."""
    async with httpx.AsyncClient() as client:
        yield client


@pytest_asyncio.fixture
async def client():
    """Клиент с транспортом приложения для интеграционных тестов API."""
    async with httpx.AsyncClient(timeout=15.0) as http_client:
        app.state.http_client = http_client
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            yield c
        if hasattr(app.state, "http_client"):
            del app.state.http_client
