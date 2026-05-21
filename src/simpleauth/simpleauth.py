from typing import TypeVar, Generic, Callable, AsyncGenerator
from uuid import UUID
from fastapi import HTTPException
from fastapi.params import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import jwt
import bcrypt

from .model import UserMixin

TableType = TypeVar("TableType", bound=UserMixin)


class SimpleAuth(Generic[TableType]):
    def __init__(self, secret: str, model: type[UserMixin],
                 get_session: Callable[..., AsyncGenerator[AsyncSession, None]],
                 token_lifespan_days: int = 30):
        self.secret = secret
        self.security = HTTPBearer()
        self.get_session = get_session
        self.model = model
        self.token_lifespan = token_lifespan_days

    @property
    def current_user(self):
        async def dependency(
                credentials: HTTPAuthorizationCredentials = Depends(self.security),
                session: AsyncSession = Depends(self.get_session)
            ) -> TableType:
            if credentials.scheme != "Bearer":
                raise HTTPException(status_code=401, detail="invalid auth scheme")
            token = credentials.credentials
            if not token:
                raise HTTPException(status_code=401, detail="missing token")

            try:
                payload = jwt.decode(token, self.secret, algorithms=["HS256"])
                user = await self.get_user_by_id(UUID(payload["sub"]), session)
                if not user:
                    raise AssertionError("couldn't find user")
                return user
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="token has expired")
            except Exception:
                raise HTTPException(status_code=401, detail="invalid token")
        return dependency

    async def _create_user(self, username: str, password: str, session: AsyncSession) -> TableType:
        if await self.get_user_by_name(username, session):
            raise HTTPException(status_code=409, detail="username already exists")
        user = self.model(
            username = username,
            password = self.hash_password(password),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def _create_token(self, username: str, password: str, session: AsyncSession) -> str:
        user = await self.get_user_with_credentials(username, password, session)
        if not user:
            raise HTTPException(status_code=401, detail="invalid credentials")
        return jwt.encode(
            {
                "sub": str(user.id),
                "exp": datetime.now() + timedelta(days=self.token_lifespan)
            },
            self.secret,
            algorithm="HS256"
        )

    async def get_user_with_credentials(self, username, password, session) -> TableType | None:
        res = await self.get_user_by_name(username, session)
        if res and self.verify_password(res.password, password):
            return res
        return None

    async def get_user_by_name(self, username: str, session: AsyncSession) -> TableType | None:
        stmt = select(self.model).where(self.model.username == username)
        return await session.scalar(stmt)

    async def get_user_by_id(self, user_id: UUID, session: AsyncSession) -> TableType | None:
        stmt = select(self.model).where(self.model.id == user_id)
        return await session.scalar(stmt)

    @staticmethod
    def hash_password(password: str):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(stored_hash: str, password: str):
        return bcrypt.checkpw(password.encode(), stored_hash.encode())
