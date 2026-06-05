import jwt
import pytest


@pytest.mark.asyncio
async def test_login(client, token):
    response = await client.get(
        "auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_malformed_auth_header(client, token):
    response = await client.get(
        "auth/me",
        headers={
            "Authorization": f"Bearer"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    response = await client.get(
        "auth/me",
        headers={
            "Authorization": token
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_expired_token(client, token):
    payload = jwt.decode(token, "secret", algorithms=["HS256"])
    payload["exp"] -= 1000000000
    token = jwt.encode(payload, "secret", algorithm="HS256")

    response = await client.get(
        "auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Token has expired"


@pytest.mark.asyncio
async def test_invalid_signature(client, token):
    payload = jwt.decode(token, "secret", algorithms=["HS256"])
    token = jwt.encode(payload, "wrong_secret", algorithm="HS256")

    response = await client.get(
        "auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"
