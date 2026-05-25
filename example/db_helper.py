from typing import Any, AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfiguredBase(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )


class Settings(ConfiguredBase):
    url: str = ""
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    model_config = SettingsConfigDict(
        env_prefix="DB_"
    )


settings = Settings()


class DBHelper:
    def __init__(self):
        self.engine = create_async_engine(
            url=settings.url,
            echo=settings.echo,
            echo_pool=settings.echo_pool,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow
        )
        self.session_maker = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False
        )

    async def dispose(self):
        await self.engine.dispose()

    async def get_session(self) -> AsyncGenerator[AsyncSession, Any]:
        async with self.session_maker() as session:
            yield session