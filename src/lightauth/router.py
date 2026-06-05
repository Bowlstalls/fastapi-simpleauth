from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .lightauth import LightAuth
from .model import UserMixin
from .schemas import UserCreateBase, UserReadBase, TokenRead, LoginRequest


def get_auth_router(auth: LightAuth, read: type[UserReadBase], create: type[UserCreateBase]):
    router = APIRouter(prefix="/auth", tags=["auth"])

    @router.post("/register", response_model=read, responses={
        409: {"description": "Username Already Exists"}
    })
    async def register(data: create, session: AsyncSession = Depends(auth._get_session)):
        return await auth._create_user(data.username, data.password, session)

    @router.post("/login", response_model=TokenRead, responses={
        401: {"description": "Login Failed"}
    })
    async def login(data: LoginRequest, session: AsyncSession = Depends(auth._get_session)):
        return {
            "access_token": await auth._create_token(data.username, data.password, session),
            "token_type": "Bearer"
        }

    @router.get("/me", response_model=read, responses={
        401: {"description": "Unauthorized"}
    })
    async def me(user: type[UserMixin] = Depends(auth.current_user)):
        return user

    return router
