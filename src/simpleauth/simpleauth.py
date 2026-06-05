from typing import TypeVar, Generic, Callable, AsyncGenerator, Union
from uuid import UUID
from fastapi import HTTPException
from fastapi.params import Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
import jwt
import bcrypt
from sqlalchemy.orm import DeclarativeBase

from .model import UserMixin

TableType = TypeVar("TableType", bound=UserMixin)


class SimpleAuth(Generic[TableType]):
    def __init__(self, secret: str, model: type[Union[UserMixin, DeclarativeBase]],
                 get_session: Callable[..., AsyncGenerator[AsyncSession, None]],
                 token_lifespan_days: int = 30):
        self._secret = secret
        self._security = HTTPBearer()
        self._get_session = get_session
        self._model = model
        self._token_lifespan = token_lifespan_days

    @property
    def current_user(self):
        async def dependency(
                credentials: HTTPAuthorizationCredentials = Security(self._security),
                session: AsyncSession = Depends(self._get_session)
            ) -> TableType:
            token = credentials.credentials

            try:
                payload = jwt.decode(token, self._secret, algorithms=["HS256"])
                user = await self._get_user_by_id(UUID(payload["sub"]), session)
                if not user:
                    raise AssertionError("couldn't find user")
                return user
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token has expired")
            except Exception:
                raise HTTPException(status_code=401, detail="Invalid token")
        return dependency

    async def _create_user(self, username: str, password: str, session: AsyncSession) -> TableType:
        if await self._get_user_by_name(username, session):
            raise HTTPException(status_code=409, detail="Username already exists")
        user = self._model(
            username = username,
            password = self._hash_password(password),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def _create_token(self, username: str, password: str, session: AsyncSession) -> str:
        user = await self._get_user_with_credentials(username, password, session)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return jwt.encode(
            {
                "sub": str(user.id),
                "exp": datetime.now(timezone.utc) + timedelta(days=self._token_lifespan)
            },
            self._secret,
            algorithm="HS256"
        )

    async def _get_user_with_credentials(self, username, password, session) -> TableType | None:
        res = await self._get_user_by_name(username, session)
        if res and self._verify_password(res.password, password):
            return res
        return None

    async def _get_user_by_name(self, username: str, session: AsyncSession) -> TableType | None:
        stmt = select(self._model).where(self._model.username == username)
        return await session.scalar(stmt)

    async def _get_user_by_id(self, user_id: UUID, session: AsyncSession) -> TableType | None:
        stmt = select(self._model).where(self._model.id == user_id)
        return await session.scalar(stmt)

    @staticmethod
    def _hash_password(password: str):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def _verify_password(stored_hash: str, password: str):
        return bcrypt.checkpw(password.encode(), stored_hash.encode())
