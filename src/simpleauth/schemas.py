from uuid import UUID
from pydantic import BaseModel


class UserReadBase(BaseModel):
    id: UUID
    name: str


class UserCreateBase(BaseModel):
    name: str
    password: str
