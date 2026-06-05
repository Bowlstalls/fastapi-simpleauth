from uuid import uuid4, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column




class UserMixin:
    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column()
