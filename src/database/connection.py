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


async def _migrate_workouts_trainer_nullable() -> None:
    """Делает workouts.trainer_id nullable, если БД была создана со старой схемой (NOT NULL)."""
    import logging
    from sqlalchemy import text
    logger = logging.getLogger(__name__)

    async with engine.connect() as conn:
        result = await conn.execute(text("PRAGMA table_info(workouts)"))
        cols = {row[1]: row for row in result.fetchall()}
        if "trainer_id" not in cols or cols["trainer_id"][3] == 0:
            return  # уже nullable — миграция не нужна

    logger.info("Запуск миграции: workouts.trainer_id → nullable")
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE workouts_migration_temp (
                id         INTEGER  NOT NULL PRIMARY KEY,
                name       VARCHAR(255) NOT NULL,
                description TEXT,
                datetime   DATETIME NOT NULL,
                duration   INTEGER  NOT NULL,
                max_participants INTEGER NOT NULL,
                trainer_id INTEGER  REFERENCES users(id),
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """))
        await conn.execute(text("INSERT INTO workouts_migration_temp SELECT * FROM workouts"))
        await conn.execute(text("DROP TABLE workouts"))
        await conn.execute(text("ALTER TABLE workouts_migration_temp RENAME TO workouts"))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_workouts_datetime ON workouts (datetime)"
        ))
    logger.info("Миграция завершена: workouts.trainer_id теперь nullable")


async def init_db() -> None:
    """
    Инициализация базы данных.
    Создаёт все таблицы, если их нет.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _migrate_workouts_trainer_nullable()


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

