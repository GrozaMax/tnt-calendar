"""
Тесты для сервисов
"""
import pytest
from datetime import datetime, timedelta

from src.services.booking_service import BookingService
from src.models import BookingStatus


class TestBookingService:
    """Тесты BookingService"""
    
    @pytest.mark.asyncio
    async def test_book_workout_success(self, db_session, test_workout, test_athlete):
        """Тест успешной записи на тренировку"""
        service = BookingService(db_session)
        
        result = await service.book_workout(
            user_id=test_athlete.id,
            workout_id=test_workout.id
        )
        
        assert result["success"] is True
        assert "booking" in result
        assert result["booking"].user_id == test_athlete.id
        assert result["booking"].workout_id == test_workout.id
    
    @pytest.mark.asyncio
    async def test_book_workout_duplicate(self, db_session, test_booking, test_athlete, test_workout):
        """Тест повторной записи на ту же тренировку"""
        service = BookingService(db_session)
        
        result = await service.book_workout(
            user_id=test_athlete.id,
            workout_id=test_workout.id
        )
        
        assert result["success"] is False
        assert "message" in result
        assert "уже записаны" in result["message"].lower() or "already booked" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_book_full_workout(self, db_session, workout_repo, test_trainer, user_repo):
        """Тест записи на заполненную тренировку"""
        # Создаем тренировку на 1 место
        workout = await workout_repo.create(
            name="Small Workout",
            datetime=datetime.now() + timedelta(hours=2),
            max_participants=1,
            trainer_id=test_trainer.id
        )
        await db_session.commit()
        
        # Создаем атлета и записываем его
        athlete1 = await user_repo.create(
            telegram_id=500001,
            first_name="Athlete1"
        )
        await db_session.commit()
        
        service = BookingService(db_session)
        result1 = await service.book_workout(athlete1.id, workout.id)
        assert result1["success"] is True
        
        # Пытаемся записать второго атлета
        athlete2 = await user_repo.create(
            telegram_id=500002,
            first_name="Athlete2"
        )
        await db_session.commit()
        
        result2 = await service.book_workout(athlete2.id, workout.id)
        assert result2["success"] is False
        assert "мест нет" in result2["message"].lower() or "full" in result2["message"].lower()
    
    @pytest.mark.asyncio
    async def test_cancel_booking_success(self, db_session, test_booking):
        """Тест успешной отмены записи"""
        service = BookingService(db_session)
        
        result = await service.cancel_booking(test_booking.id)
        
        assert result["success"] is True
        assert result["booking"].status == BookingStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_cancel_nonexistent_booking(self, db_session):
        """Тест отмены несуществующей записи"""
        service = BookingService(db_session)
        
        result = await service.cancel_booking(999999)
        
        assert result["success"] is False
        assert "не найдена" in result["message"].lower() or "not found" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_get_user_upcoming_bookings(self, db_session, test_athlete, workout_repo, test_trainer, booking_repo):
        """Тест получения предстоящих записей пользователя"""
        # Создаем тренировки в будущем и прошлом
        future_workout = await workout_repo.create(
            name="Future Workout",
            datetime=datetime.now() + timedelta(days=1),
            trainer_id=test_trainer.id
        )
        past_workout = await workout_repo.create(
            name="Past Workout",
            datetime=datetime.now() - timedelta(days=1),
            trainer_id=test_trainer.id
        )
        await db_session.commit()
        
        # Записываем пользователя на обе
        await booking_repo.create(test_athlete.id, future_workout.id)
        await booking_repo.create(test_athlete.id, past_workout.id)
        await db_session.commit()
        
        service = BookingService(db_session)
        bookings = await service.get_user_upcoming_bookings(test_athlete.id)
        
        # Должна быть только будущая тренировка
        assert len(bookings) >= 1
        workout_ids = [b.workout_id for b in bookings]
        assert future_workout.id in workout_ids
    
    @pytest.mark.asyncio
    async def test_bookings_sorted_by_date(self, db_session, test_athlete, workout_repo, test_trainer, booking_repo):
        """Тест сортировки записей по дате (ближайшие первыми)"""
        # Создаем тренировки в разное время
        workout_later = await workout_repo.create(
            name="Later Workout",
            datetime=datetime.now() + timedelta(days=3),
            trainer_id=test_trainer.id
        )
        workout_soon = await workout_repo.create(
            name="Soon Workout",
            datetime=datetime.now() + timedelta(hours=5),
            trainer_id=test_trainer.id
        )
        workout_middle = await workout_repo.create(
            name="Middle Workout",
            datetime=datetime.now() + timedelta(days=1),
            trainer_id=test_trainer.id
        )
        await db_session.commit()
        
        # Записываем в "неправильном" порядке
        await booking_repo.create(test_athlete.id, workout_later.id)
        await booking_repo.create(test_athlete.id, workout_soon.id)
        await booking_repo.create(test_athlete.id, workout_middle.id)
        await db_session.commit()
        
        service = BookingService(db_session)
        bookings = await service.get_user_active_bookings(test_athlete.id)
        
        # Проверяем что отсортированы (ближайшие первыми)
        assert len(bookings) >= 3
        dates = [b.workout.datetime for b in bookings]
        assert dates == sorted(dates), "Записи должны быть отсортированы по дате"
    
    @pytest.mark.asyncio
    async def test_book_full_workout_error_message(self, db_session, workout_repo, test_trainer, user_repo):
        """Тест сообщения об ошибке при записи на заполненную тренировку"""
        # Создаем тренировку на 1 место
        workout = await workout_repo.create(
            name="Full Workout Test",
            datetime=datetime.now() + timedelta(hours=3),
            max_participants=1,
            trainer_id=test_trainer.id
        )
        await db_session.commit()
        
        # Заполняем
        athlete1 = await user_repo.create(telegram_id=600001, first_name="First")
        await db_session.commit()
        
        service = BookingService(db_session)
        await service.book_workout(athlete1.id, workout.id)
        
        # Пытаемся записать второго
        athlete2 = await user_repo.create(telegram_id=600002, first_name="Second")
        await db_session.commit()
        
        result = await service.book_workout(athlete2.id, workout.id)
        
        assert result["success"] is False
        # Проверяем что сообщение информативное
        assert "мест нет" in result["message"].lower() or "максимум" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_booking_limit_error_message(self, db_session, workout_repo, test_trainer, test_athlete):
        """Тест сообщения об ошибке при превышении лимита записей в день"""
        # Создаем 3 тренировки на один день (сегодня)
        # Use fixed time tomorrow morning so all 3 workouts land on the same day
        base_dt = (datetime.now() + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
        workouts = []
        for i in range(3):
            workout = await workout_repo.create(
                name=f"Workout {i}",
                datetime=base_dt + timedelta(hours=i),
                max_participants=10,
                trainer_id=test_trainer.id
            )
            workouts.append(workout)
        await db_session.commit()
        
        service = BookingService(db_session)
        
        # Записываемся на первые две (лимит = 2)
        await service.book_workout(test_athlete.id, workouts[0].id)
        await service.book_workout(test_athlete.id, workouts[1].id)
        
        # Третья должна быть с ошибкой лимита
        result = await service.book_workout(test_athlete.id, workouts[2].id)
        
        assert result["success"] is False
        assert "лимит" in result["message"].lower() or "уже записаны" in result["message"].lower()

