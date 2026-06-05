from uuid import UUID
from pydantic import BaseModel, Field


class UserReadBase(BaseModel):
    id: UUID
    username: str


class UserCreateBase(BaseModel):
    username: str
    password: str


class TokenRead(BaseModel):
    token: str
    token_type: str = Field(alias="token-type")
