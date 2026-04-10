"""
Конфигурация pytest и общие фикстуры
"""
import asyncio
import pytest
import pytest_asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from unittest.mock import patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import ASGITransport, AsyncClient

from src.models.base import Base
from src.models import User, UserRole, Workout, Booking, BookingStatus, AppSetting  # noqa: F401
from src.database.repositories import UserRepository, WorkoutRepository, BookingRepository
from src.database import get_session
from web.api.auth import get_current_user
from web.main import app


# Настройка для асинхронных тестов
@pytest.fixture(scope="session")
def event_loop():
    """Создаем event loop для всей сессии тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


pytest_plugins = ("pytest_asyncio",)


@pytest_asyncio.fixture
async def db_engine():
    """Создаем тестовую БД в памяти"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Создаем сессию БД для каждого теста"""
    async_session = async_sessionmaker(
        db_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def user_repo(db_session):
    """Репозиторий пользователей"""
    return UserRepository(db_session)


@pytest_asyncio.fixture
async def workout_repo(db_session):
    """Репозиторий тренировок"""
    return WorkoutRepository(db_session)


@pytest_asyncio.fixture
async def booking_repo(db_session):
    """Репозиторий записей"""
    return BookingRepository(db_session)


# Фикстуры с тестовыми данными
@pytest_asyncio.fixture
async def test_admin(user_repo, db_session):
    """Создаем тестового админа"""
    admin = await user_repo.create(
        telegram_id=111111,
        username="test_admin",
        first_name="Test",
        last_name="Admin",
        role=UserRole.ADMIN
    )
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def test_trainer(user_repo, db_session):
    """Создаем тестового тренера"""
    trainer = await user_repo.create(
        telegram_id=222222,
        username="test_trainer",
        first_name="Test",
        last_name="Trainer",
        role=UserRole.TRAINER
    )
    await db_session.commit()
    await db_session.refresh(trainer)
    return trainer


@pytest_asyncio.fixture
async def test_athlete(user_repo, db_session):
    """Создаем тестового атлета"""
    athlete = await user_repo.create(
        telegram_id=333333,
        username="test_athlete",
        first_name="Test",
        last_name="Athlete",
        role=UserRole.ATHLETE
    )
    await db_session.commit()
    await db_session.refresh(athlete)
    return athlete


@pytest_asyncio.fixture
async def test_workout(workout_repo, test_trainer, db_session):
    """Создаем тестовую тренировку"""
    workout = await workout_repo.create(
        name="CrossFit",
        description="Test workout",
        datetime=datetime.now() + timedelta(hours=2),
        duration=60,
        max_participants=10,
        trainer_id=test_trainer.id
    )
    await db_session.commit()
    await db_session.refresh(workout)
    return workout


@pytest_asyncio.fixture
async def test_booking(booking_repo, test_workout, test_athlete, db_session):
    """Создаем тестовую запись"""
    booking = await booking_repo.create(
        user_id=test_athlete.id,
        workout_id=test_workout.id
    )
    await db_session.commit()
    await db_session.refresh(booking)
    return booking


# API тесты - моки и клиент

_API_MODULES = [
    'web.api.workouts',
    'web.api.users',
    'web.api.schedule_template',
    'web.api.business_settings',
]


def _make_session_patcher(db_session):
    """Создаёт контекстный менеджер, который патчит get_session во всех API модулях."""
    @asynccontextmanager
    async def _mock():
        yield db_session

    patches = [patch(f'{mod}.get_session', _mock) for mod in _API_MODULES]

    class _Patcher:
        def __enter__(self):
            for p in patches:
                p.start()
            return self
        def __exit__(self, *_):
            for p in patches:
                p.stop()

    return _Patcher()


@pytest_asyncio.fixture
async def api_client_admin(db_session, test_admin):
    """Async HTTP-клиент к приложению с подменой пользователя-админа и сессии БД."""

    async def _user():
        return test_admin

    app.dependency_overrides[get_current_user] = _user
    transport = ASGITransport(app=app)
    with _make_session_patcher(db_session):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def api_client_trainer(db_session, test_trainer):
    async def _user():
        return test_trainer

    app.dependency_overrides[get_current_user] = _user
    transport = ASGITransport(app=app)
    with _make_session_patcher(db_session):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def api_client_athlete(db_session, test_athlete):
    async def _user():
        return test_athlete

    app.dependency_overrides[get_current_user] = _user
    transport = ASGITransport(app=app)
    with _make_session_patcher(db_session):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    app.dependency_overrides.clear()

