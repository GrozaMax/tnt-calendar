"""
Сервис для работы с записями
"""
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.repositories import BookingRepository, WorkoutRepository
from src.models import BookingStatus
from src.utils.validators import (
    validate_booking_time,
    can_book_workout,
    validate_workout_slot
)


class BookingService:
    """Сервис для управления записями на тренировки"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.booking_repo = BookingRepository(session)
        self.workout_repo = WorkoutRepository(session)
    
    async def create_booking(
        self,
        user_id: int,
        workout_id: int
    ) -> tuple[bool, str, object]:
        """
        Создать запись на тренировку с валидацией всех ограничений.
        
        Returns:
            tuple[bool, str, Booking | None]: (успех, сообщение, запись)
        """
        # Получаем тренировку
        workout = await self.workout_repo.get_by_id(workout_id, load_relations=True)
        if not workout:
            return False, "❌ Тренировка не найдена", None
        
        # Проверка времени записи (только сегодня и завтра)
        is_valid_time, time_error = validate_booking_time(workout.datetime)
        if not is_valid_time:
            return False, time_error, None
        
        # Проверка, не записан ли уже пользователь
        existing_booking = await self.booking_repo.get_by_user_and_workout(
            user_id, workout_id
        )
        if existing_booking:
            if existing_booking.is_active():
                return False, "ℹ️ Вы уже записаны на эту тренировку", None
            else:
                # Если запись была отменена, реактивируем её
                existing_booking.activate()
                await self.session.commit()
                return True, "✅ Запись восстановлена успешно", existing_booking
        
        # Проверка лимита записей в день (максимум 2)
        workout_date = workout.datetime.date()
        bookings_count = await self.booking_repo.count_active_bookings_by_date(
            user_id, workout_date
        )
        can_book, limit_error = can_book_workout(bookings_count)
        if not can_book:
            return False, limit_error, None
        
        # Проверка свободных мест
        has_slots, slots_error = validate_workout_slot(
            workout.current_participants,
            workout.max_participants
        )
        if not has_slots:
            return False, slots_error, None
        
        # Создание записи
        booking = await self.booking_repo.create(
            user_id=user_id,
            workout_id=workout_id,
            status=BookingStatus.ACTIVE
        )
        
        await self.session.commit()
        
        return True, "✅ Запись создана успешно", booking
    
    async def cancel_booking(
        self,
        booking_id: int,
        user_id: int
    ) -> tuple[bool, str]:
        """
        Отменить запись.
        
        Returns:
            tuple[bool, str]: (успех, сообщение)
        """
        booking = await self.booking_repo.get_by_id(booking_id)
        
        if not booking:
            return False, "❌ Запись не найдена"
        
        # Проверка, что это запись текущего пользователя
        if booking.user_id != user_id:
            return False, "❌ Это не ваша запись"
        
        if not booking.is_active():
            return False, "ℹ️ Запись уже отменена"
        
        # Отмена записи
        booking.cancel()
        await self.session.commit()
        
        return True, "✅ Запись успешно отменена"
    
    async def get_user_active_bookings(self, user_id: int):
        """Получить все активные записи пользователя"""
        bookings = await self.booking_repo.get_user_bookings(
            user_id,
            status=BookingStatus.ACTIVE,
            load_relations=True
        )
        
        # Фильтрация только будущих тренировок
        from datetime import datetime
        now = datetime.now()
        future_bookings = [
            b for b in bookings if b.workout.datetime > now
        ]
        
        return future_bookings

