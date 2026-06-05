# fastapi-simpleauth

A lightweight JWT authentication library for FastAPI and SQLAlchemy.
Built with simplicity in mind for small and medium FastAPI projects.

Features:
* JWT authentication
* Secure password hashing with bcrypt
* User registration and login endpoints
* Current-user dependency injection
* Extendable SQLAlchemy user models
* Extendable Pydantic schemas
* Async SQLAlchemy support

## Installation

```bash
pip install fastapi-simpleauth
```

---

## Quick start

### 1. Define your user model

SimpleAuth requires 'UserMixin', but everything else is completely up to you
```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from simpleauth import UserMixin


class Base(DeclarativeBase):
    pass


class User(UserMixin, Base):
    __tablename__ = "users"

    extra_stuff: Mapped[str] = mapped_column(default="no extra stuff here")
```

---

### 2. Optional: extend your response schema

You can add fields that you want returned in API responses:

```python
from simpleauth.schemas import UserReadBase


class UserReadSchema(UserReadBase):
    extra_stuff: str
```

---

### 3. Create a session dependency

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from typing import AsyncGenerator, Any

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
session_maker = async_sessionmaker(engine)


async def get_session() -> AsyncGenerator[AsyncSession, Any]:
    async with session_maker() as session:
        yield session
```

---

### 4. Set up SimpleAuth

```python
from simpleauth import SimpleAuth

auth = SimpleAuth[User](
    secret="your-secret-key",
    model=User,
    get_session=get_session,
)
```
Optionally configure token lifespan via `token_lifespan_days`

---

### 5. Add the router

```python
from simpleauth import get_auth_router
from simpleauth.schemas import UserCreateBase

app.include_router(
    get_auth_router(
        auth,
        UserReadSchema,
        UserCreateBase,
    )
)
```

---

## Using authentication in routes

You protect routes using a FastAPI dependency:

```python
from fastapi import Depends

@app.get("/hello")
async def hello(user: User = Depends(auth.current_user)):
    return f"Hello, {user.username}"
```

That dependency will:

* read the Bearer token
* validate the JWT
* load the user from the database
* inject the full SQLAlchemy user object

---

## Endpoints

### Register

```
POST /auth/register
```

```json
{
  "username": "...",
  "password": "..."
}
```

Returns the created user.

---

### Login

```
POST /auth/login
```

```json
{
  "username": "...",
  "password": "..."
}
```

Returns:

```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer"
}
```

---

### Current user

```
GET /auth/me
```

Requires:

```
Authorization: Bearer <token>
```

Returns the current user.

---

## Security notes

* Passwords are hashed using bcrypt
* JWT tokens include:
  * `sub` → user ID
  * `exp` → expiration timestamp
* Default token lifetime: 30 days

---

## License

MIT
