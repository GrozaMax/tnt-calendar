"""
Конфигурация pytest и общие фикстуры
"""
import asyncio
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from src.models.base import Base
from src.models import User, UserRole, Workout, Booking, BookingStatus
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


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
async def user_repo(db_session):
    """Репозиторий пользователей"""
    return UserRepository(db_session)


@pytest.fixture
async def workout_repo(db_session):
    """Репозиторий тренировок"""
    return WorkoutRepository(db_session)


@pytest.fixture
async def booking_repo(db_session):
    """Репозиторий записей"""
    return BookingRepository(db_session)


# Фикстуры с тестовыми данными
@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
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

@pytest.fixture
def override_get_session(db_session):
    """Переопределяем get_session для API тестов"""
    async def _get_session_override():
        yield db_session
    return _get_session_override


@pytest.fixture
def override_get_current_user_admin(test_admin):
    """Переопределяем get_current_user для админа"""
    async def _get_current_user_override():
        return test_admin
    return _get_current_user_override


@pytest.fixture
def override_get_current_user_trainer(test_trainer):
    """Переопределяем get_current_user для тренера"""
    async def _get_current_user_override():
        return test_trainer
    return _get_current_user_override


@pytest.fixture
def override_get_current_user_athlete(test_athlete):
    """Переопределяем get_current_user для атлета"""
    async def _get_current_user_override():
        return test_athlete
    return _get_current_user_override


@pytest.fixture
def api_client_admin(override_get_session, override_get_current_user_admin):
    """Тестовый API клиент с правами админа"""
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user_admin
    
    client = TestClient(app)
    yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def api_client_trainer(override_get_session, override_get_current_user_trainer):
    """Тестовый API клиент с правами тренера"""
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user_trainer
    
    client = TestClient(app)
    yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def api_client_athlete(override_get_session, override_get_current_user_athlete):
    """Тестовый API клиент с правами атлета"""
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user_athlete
    
    client = TestClient(app)
    yield client
    
    app.dependency_overrides.clear()

