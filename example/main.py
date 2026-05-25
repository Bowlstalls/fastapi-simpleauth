from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.params import Depends
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

from db_helper import DBHelper
from src.simpleauth.model import UserMixin
from src.simpleauth.router import get_auth_router
from src.simpleauth.schemas import UserReadBase, UserCreateBase
from src.simpleauth.simpleauth import SimpleAuth


class Base(DeclarativeBase):
    pass


class User(UserMixin, Base):
    __tablename__ = "users"

    extra_stuff: Mapped[str] = mapped_column(default="no extra stuff here")


class UserReadSchema(UserReadBase):
    extra_stuff: str


db = DBHelper()
auth = SimpleAuth[User]("abc123abc123abc123abc123abc123abc123abc123abc123abc123", User, db.get_session)
auth_router = get_auth_router(auth, UserReadSchema, UserCreateBase)


@asynccontextmanager
async def lifespan(_):
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await db.dispose()

app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
@app.get("/hello")
async def hello(user: User = Depends(auth.current_user)):
    return f"Hello, {user.username}"
