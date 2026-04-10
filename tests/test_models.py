"""
Тесты для моделей
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models import User, UserRole, Workout, Booking, BookingStatus


class TestUser:
    """Тесты модели User"""
    
    @pytest.mark.asyncio
    async def test_create_user(self, user_repo, db_session):
        """Тест создания пользователя"""
        user = await user_repo.create(
            telegram_id=999999,
            username="testuser",
            first_name="Test",
            last_name="User",
            role=UserRole.ATHLETE
        )
        await db_session.commit()
        
        assert user.id is not None
        assert user.telegram_id == 999999
        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.role == UserRole.ATHLETE
    
    @pytest.mark.asyncio
    async def test_user_roles(self, test_admin, test_trainer, test_athlete):
        """Тест ролей пользователей"""
        assert test_admin.is_admin() is True
        assert test_admin.is_trainer() is False
        
        assert test_trainer.is_admin() is False
        assert test_trainer.is_trainer() is True
        
        assert test_athlete.is_admin() is False
        assert test_athlete.is_trainer() is False
    
    @pytest.mark.asyncio
    async def test_user_full_name(self, user_repo, db_session):
        """Тест формирования полного имени"""
        user1 = await user_repo.create(
            telegram_id=100001,
            first_name="John",
            last_name="Doe"
        )
        await db_session.commit()
        assert user1.full_name == "John Doe"
        
        user2 = await user_repo.create(
            telegram_id=100002,
            first_name="Jane"
        )
        await db_session.commit()
        assert user2.full_name == "Jane"


class TestWorkout:
    """Тесты модели Workout"""
    
    @pytest.mark.asyncio
    async def test_create_workout(self, workout_repo, test_trainer, db_session):
        """Тест создания тренировки"""
        workout_datetime = datetime.now() + timedelta(days=1)
        workout = await workout_repo.create(
            name="Yoga",
            description="Morning yoga",
            datetime=workout_datetime,
            duration=60,
            max_participants=15,
            trainer_id=test_trainer.id
        )
        await db_session.commit()
        
        assert workout.id is not None
        assert workout.name == "Yoga"
        assert workout.duration == 60
        assert workout.max_participants == 15
        assert workout.trainer_id == test_trainer.id
    
    @pytest.mark.asyncio
    async def test_workout_current_participants(self, test_workout, test_athlete, booking_repo, db_session):
        """Подсчёт участников: hybrid property при загруженных bookings и async-запрос к БД."""
        workout_id = test_workout.id

        async def load_workout() -> Workout:
            # После commit новая запись в БД: без populate_existing сессия может вернуть
            # закэшированный Workout с пустым bookings (identity map).
            res = await db_session.execute(
                select(Workout)
                .where(Workout.id == workout_id)
                .options(selectinload(Workout.bookings))
                .execution_options(populate_existing=True)
            )
            return res.scalar_one()

        w = await load_workout()
        assert w.current_participants == 0
        assert await w.get_current_participants_async(db_session) == 0

        await booking_repo.create(
            user_id=test_athlete.id,
            workout_id=workout_id,
        )
        await db_session.commit()

        w = await load_workout()
        assert w.current_participants == 1
        assert await w.get_current_participants_async(db_session) == 1

    @pytest.mark.asyncio
    async def test_workout_is_full(
        self, workout_repo, user_repo, test_trainer, booking_repo, db_session
    ):
        """Заполненность: is_full / has_free_slots при загруженных bookings + сверка с COUNT в БД."""
        workout = await workout_repo.create(
            name="Small Class",
            datetime=datetime.now() + timedelta(hours=2),
            max_participants=2,
            trainer_id=test_trainer.id,
        )
        await db_session.commit()
        workout_id = workout.id

        a1 = await user_repo.create(telegram_id=400001, first_name="Athlete1")
        a2 = await user_repo.create(telegram_id=400002, first_name="Athlete2")
        await db_session.commit()

        async def load_workout() -> Workout:
            res = await db_session.execute(
                select(Workout)
                .where(Workout.id == workout_id)
                .options(selectinload(Workout.bookings))
                .execution_options(populate_existing=True)
            )
            return res.scalar_one()

        w = await load_workout()
        assert w.is_full is False
        assert w.has_free_slots is True

        await booking_repo.create(user_id=a1.id, workout_id=workout_id)
        await db_session.commit()
        w = await load_workout()
        assert w.is_full is False
        assert w.has_free_slots is True
        assert await w.get_current_participants_async(db_session) == 1

        await booking_repo.create(user_id=a2.id, workout_id=workout_id)
        await db_session.commit()
        w = await load_workout()
        assert w.current_participants == 2
        assert await w.get_current_participants_async(db_session) == 2
        assert w.is_full is True
        assert w.has_free_slots is False


class TestBooking:
    """Тесты модели Booking"""
    
    @pytest.mark.asyncio
    async def test_create_booking(self, booking_repo, test_workout, test_athlete, db_session):
        """Тест создания записи"""
        booking = await booking_repo.create(
            user_id=test_athlete.id,
            workout_id=test_workout.id
        )
        await db_session.commit()
        
        assert booking.id is not None
        assert booking.user_id == test_athlete.id
        assert booking.workout_id == test_workout.id
        assert booking.status == BookingStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_booking_status(self, test_booking, db_session):
        """Тест статусов записи"""
        assert test_booking.status == BookingStatus.ACTIVE
        assert test_booking.is_active is True
        
        # Отменяем запись
        test_booking.status = BookingStatus.CANCELLED
        await db_session.commit()
        
        assert test_booking.is_active is False

