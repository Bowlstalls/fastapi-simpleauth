import pytest


@pytest.mark.asyncio
async def test_register(client):
    response = await client.post(
        "auth/register",
        json={
            "username": "name",
            "password": "password"
        }
    )
    assert response.status_code == 200
    assert response.json()["username"] == "name"


@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    await client.post(
        "auth/register",
        json={
            "username": "name",
            "password": "password"
        }
    )
    response = await client.post(
        "auth/register",
        json={
            "username": "name",
            "password": "password"
        }
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "username already exists"
