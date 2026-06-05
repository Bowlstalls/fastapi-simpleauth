import pytest


@pytest.mark.asyncio
async def test_login(client, registered_user):
    response = await client.post(
        "auth/login",
        json=registered_user
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_invalid_credentials(client):
    response = await client.post(
        "auth/login",
        json={
            "username": "wrong_username",
            "password": "wrong_password"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
