"""
Подключение к базе данных
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import Pool

from src.config import Config
from src.models.base import Base

# Создание engine
engine: AsyncEngine = create_async_engine(
    Config.DATABASE_URL,
    echo=False,  # Отключаем SQL логирование (слишком много вывода)
    future=True,
)

# Включаем foreign keys для SQLite
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Включаем foreign keys для SQLite при каждом подключении"""
    import logging
    logger = logging.getLogger(__name__)
    
    if "sqlite" in Config.DATABASE_URL:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        # Проверяем, что включилось
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()
        logger.info(f"SQLite PRAGMA foreign_keys установлен: {result[0] if result else 'неизвестно'}")
        cursor.close()

# Session maker
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """
    Инициализация базы данных.
    Создаёт все таблицы, если их нет.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager для получения сессии БД.
    
    Usage:
        async with get_session() as session:
            # работа с сессией
            await session.commit()
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

