import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from tests.main import app, engine, Base


@pytest_asyncio.fixture
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test/") as client:
        yield client
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def registered_user(client):
    await client.post(
        "auth/register",
        json={
            "username": "name",
            "password": "password"
        }
    )
    return {
        "username": "name",
        "password": "password"
    }

@pytest_asyncio.fixture
async def token(client, registered_user):
    response = await client.post(
        "auth/login",
        json=registered_user
    )
    return response.json()["token"]