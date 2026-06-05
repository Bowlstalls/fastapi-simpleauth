from typing import AsyncGenerator, Any
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from src.lightauth.model import UserMixin
from src.lightauth.router import get_auth_router
from src.lightauth.schemas import UserReadBase, UserCreateBase
from src.lightauth.lightauth import LightAuth


class Base(DeclarativeBase):
    pass


class User(UserMixin, Base):
    __tablename__ = "users"


engine = create_async_engine("sqlite+aiosqlite:///:memory:")
session_maker = async_sessionmaker(engine)


async def get_session() -> AsyncGenerator[AsyncSession, Any]:
    async with session_maker() as session:
        yield session


auth = LightAuth[User]("secret", User, get_session)
app = FastAPI()
app.include_router(get_auth_router(auth, UserReadBase, UserCreateBase))
