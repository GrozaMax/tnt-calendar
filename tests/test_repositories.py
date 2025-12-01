"""
Тесты для репозиториев
"""
import pytest
from datetime import datetime, date, timedelta

from src.models import UserRole, BookingStatus


class TestUserRepository:
    """Тесты UserRepository"""
    
    @pytest.mark.asyncio
    async def test_get_by_telegram_id(self, user_repo, test_athlete):
        """Тест получения пользователя по telegram_id"""
        user = await user_repo.get_by_telegram_id(test_athlete.telegram_id)
        
        assert user is not None
        assert user.id == test_athlete.id
        assert user.telegram_id == test_athlete.telegram_id
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, user_repo, test_admin):
        """Тест получения пользователя по ID"""
        user = await user_repo.get_by_id(test_admin.id)
        
        assert user is not None
        assert user.id == test_admin.id
        assert user.role == UserRole.ADMIN
    
    @pytest.mark.asyncio
    async def test_get_all(self, user_repo, test_admin, test_trainer, test_athlete):
        """Тест получения всех пользователей"""
        users = await user_repo.get_all()
        
        assert len(users) >= 3
        user_ids = [u.id for u in users]
        assert test_admin.id in user_ids
        assert test_trainer.id in user_ids
        assert test_athlete.id in user_ids
    
    @pytest.mark.asyncio
    async def test_update_role(self, user_repo, test_athlete, db_session):
        """Тест обновления роли пользователя"""
        assert test_athlete.role == UserRole.ATHLETE
        
        updated_user = await user_repo.update(
            test_athlete.id,
            {"role": UserRole.TRAINER}
        )
        await db_session.commit()
        
        assert updated_user.role == UserRole.TRAINER


class TestWorkoutRepository:
    """Тесты WorkoutRepository"""
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, workout_repo, test_workout):
        """Тест получения тренировки по ID"""
        workout = await workout_repo.get_by_id(test_workout.id)
        
        assert workout is not None
        assert workout.id == test_workout.id
        assert workout.name == test_workout.name
    
    @pytest.mark.asyncio
    async def test_get_by_date(self, workout_repo, test_trainer, db_session):
        """Тест получения тренировок по дате"""
        target_date = date.today() + timedelta(days=3)
        
        # Создаем 2 тренировки на одну дату
        workout1 = await workout_repo.create(
            name="Morning Workout",
            datetime=datetime.combine(target_date, datetime.min.time().replace(hour=8)),
            trainer_id=test_trainer.id
        )
        workout2 = await workout_repo.create(
            name="Evening Workout",
            datetime=datetime.combine(target_date, datetime.min.time().replace(hour=18)),
            trainer_id=test_trainer.id
        )
        await db_session.commit()
        
        workouts = await workout_repo.get_by_date(target_date)
        
        assert len(workouts) == 2
        workout_ids = [w.id for w in workouts]
        assert workout1.id in workout_ids
        assert workout2.id in workout_ids
    
    @pytest.mark.asyncio
    async def test_get_by_date_range(self, workout_repo, test_trainer, db_session):
        """Тест получения тренировок по диапазону дат"""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)
        
        # Создаем тренировки в диапазоне и вне его
        workout_in_range = await workout_repo.create(
            name="Workout In Range",
            datetime=datetime.combine(start_date + timedelta(days=3), datetime.min.time().replace(hour=10)),
            trainer_id=test_trainer.id
        )
        workout_out_range = await workout_repo.create(
            name="Workout Out Range",
            datetime=datetime.combine(start_date + timedelta(days=10), datetime.min.time().replace(hour=10)),
            trainer_id=test_trainer.id
        )
        await db_session.commit()
        
        workouts = await workout_repo.get_by_date_range(start_date, end_date)
        
        workout_ids = [w.id for w in workouts]
        assert workout_in_range.id in workout_ids
        assert workout_out_range.id not in workout_ids
    
    @pytest.mark.asyncio
    async def test_delete_workout(self, workout_repo, test_workout, db_session):
        """Тест удаления тренировки"""
        workout_id = test_workout.id
        
        success = await workout_repo.delete(workout_id)
        await db_session.commit()
        
        assert success is True
        
        # Проверяем, что тренировка удалена
        deleted_workout = await workout_repo.get_by_id(workout_id)
        assert deleted_workout is None


class TestBookingRepository:
    """Тесты BookingRepository"""
    
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
    async def test_get_user_bookings(self, booking_repo, test_booking, test_athlete):
        """Тест получения записей пользователя"""
        bookings = await booking_repo.get_user_bookings(test_athlete.id)
        
        assert len(bookings) >= 1
        booking = bookings[0]
        assert booking.user_id == test_athlete.id
    
    @pytest.mark.asyncio
    async def test_get_workout_bookings(self, booking_repo, test_booking, test_workout):
        """Тест получения записей на тренировку"""
        bookings = await booking_repo.get_workout_bookings(test_workout.id)
        
        assert len(bookings) >= 1
        booking = bookings[0]
        assert booking.workout_id == test_workout.id
    
    @pytest.mark.asyncio
    async def test_cancel_booking(self, booking_repo, test_booking, db_session):
        """Тест отмены записи"""
        assert test_booking.status == BookingStatus.ACTIVE
        
        cancelled_booking = await booking_repo.cancel(test_booking.id)
        await db_session.commit()
        
        assert cancelled_booking.status == BookingStatus.CANCELLED
        assert cancelled_booking.is_active is False
    
    @pytest.mark.asyncio
    async def test_check_duplicate_booking(self, booking_repo, test_booking, test_athlete, test_workout):
        """Тест проверки дубликата записи"""
        # Пытаемся создать дубликат
        existing = await booking_repo.get_user_workout_booking(
            test_athlete.id,
            test_workout.id,
            status=BookingStatus.ACTIVE
        )
        
        assert existing is not None
        assert existing.id == test_booking.id

