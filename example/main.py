from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any
from fastapi import FastAPI
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from simpleauth import SimpleAuth, UserMixin, get_auth_router
from simpleauth.schemas import UserReadBase, UserCreateBase


class Base(DeclarativeBase):
    pass


class User(UserMixin, Base):
    __tablename__ = "users"

    extra_stuff: Mapped[str] = mapped_column(default="no extra stuff here")


class UserReadSchema(UserReadBase):
    extra_stuff: str


DB_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DB_URL)
session_maker = async_sessionmaker(engine)


async def get_session() -> AsyncGenerator[AsyncSession, Any]:
    async with session_maker() as session:
        yield session


auth = SimpleAuth[User]("secret", User, get_session)
auth_router = get_auth_router(auth, UserReadSchema, UserCreateBase)


@asynccontextmanager
async def lifespan(_):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
@app.get("/hello")
async def hello(user: User = Depends(auth.current_user)):
    return f"Hello, {user.username}"
