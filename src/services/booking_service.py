"""
Сервис для работы с записями
"""
from __future__ import annotations

from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.repositories import BookingRepository, WorkoutRepository
from src.locales import get_text
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
        workout_id: int,
        lang: str = 'ru'
    ) -> tuple[bool, str, object]:
        """
        Создать запись на тренировку с валидацией всех ограничений.
        
        Returns:
            tuple[bool, str, Booking | None]: (успех, сообщение, запись)
        """
        # Получаем тренировку
        workout = await self.workout_repo.get_by_id(workout_id, load_relations=True)
        if not workout:
            return False, get_text('schedule.workout_not_found', lang), None
        
        # Проверка времени записи (только сегодня и завтра)
        is_valid_time, time_error = validate_booking_time(workout.datetime, lang=lang)
        if not is_valid_time:
            return False, time_error, None
        
        # Проверка, не записан ли уже пользователь
        existing_booking = await self.booking_repo.get_by_user_and_workout(
            user_id, workout_id
        )
        if existing_booking:
            if existing_booking.is_active:
                return False, get_text('booking.already_booked', lang), None
            else:
                # Если запись была отменена, реактивируем её
                existing_booking.activate()
                await self.session.commit()
                return True, get_text('booking.restored', lang), existing_booking
        
        # Проверка дневного лимита (макс. 2 тренировки в день)
        day_bookings = await self.booking_repo.get_active_bookings_by_date(
            user_id, workout.datetime.date()
        )
        can_book, limit_error = can_book_workout(len(day_bookings), lang=lang)
        if not can_book:
            return False, limit_error, None

        # Проверка свободных мест - используем прямой подсчет из БД
        current_count = await workout.get_current_participants_async(self.session)
        has_slots, slots_error = validate_workout_slot(
            current_count,
            workout.max_participants,
            lang=lang
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
        
        return True, get_text('booking.created', lang), booking
    
    async def cancel_booking(
        self,
        booking_id: int,
        user_id: int = None,
        lang: str = 'ru'
    ) -> tuple[bool, str] | dict:
        """
        Отменить запись.
        
        Returns:
            tuple[bool, str] или dict (для тестов): (успех, сообщение) или {"success": bool, "message": str, "booking": Booking}
        """
        booking = await self.booking_repo.get_by_id(booking_id)
        
        if not booking:
            message = get_text('booking.not_found', lang)
            if user_id is None:
                return {"success": False, "message": message, "booking": None}
            return False, message
        
        # Проверка, что это запись текущего пользователя (только если user_id передан)
        if user_id is not None and booking.user_id != user_id:
            message = get_text('booking.not_yours', lang)
            return False, message
        
        if not booking.is_active:
            message = get_text('booking.already_cancelled', lang)
            if user_id is None:
                return {"success": False, "message": message, "booking": booking}
            return False, message
        
        # Отмена записи
        booking.cancel()
        await self.session.commit()
        
        message = get_text('booking.cancel_success', lang)
        if user_id is None:
            return {"success": True, "message": message, "booking": booking}
        return True, message
    
    async def cancel_booking_by_trainer(self, booking_id: int, trainer_id: int, is_admin: bool = False, lang: str = 'ru') -> tuple[bool, str]:
        """
        Отменить запись атлета от имени тренера (или администратора).
        Тренер может отменить только запись на свою тренировку; админ — на любую.
        """
        booking = await self.booking_repo.get_by_id(booking_id, load_relations=True)
        if not booking:
            return False, get_text('booking.not_found', lang)
        if not is_admin and booking.workout.trainer_id != trainer_id:
            return False, get_text('booking.not_your_workout', lang)
        if not booking.is_active:
            return False, get_text('booking.already_cancelled', lang)
        booking.cancel()
        await self.session.commit()
        return True, get_text('booking.athlete_removed', lang)

    async def get_user_active_bookings(self, user_id: int):
        """Получить все активные записи пользователя (отсортированные по дате)"""
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
        
        # Сортировка по дате/времени тренировки (ближайшие первыми)
        future_bookings.sort(key=lambda b: b.workout.datetime)
        
        return future_bookings
    
    # Aliases и обертки для тестов
    async def book_workout(self, user_id: int, workout_id: int, lang: str = 'ru') -> dict:
        """
        Alias для create_booking, возвращает dict для совместимости с тестами
        
        Returns:
            dict: {"success": bool, "message": str, "booking": Booking | None}
        """
        success, message, booking = await self.create_booking(user_id, workout_id, lang)
        return {
            "success": success,
            "message": message,
            "booking": booking
        }
    
    async def get_user_upcoming_bookings(self, user_id: int):
        """Alias для get_user_active_bookings"""
        return await self.get_user_active_bookings(user_id)
