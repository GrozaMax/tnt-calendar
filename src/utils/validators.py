"""
Валидаторы для бизнес-логики
"""
from __future__ import annotations

from datetime import datetime, date, timedelta

from src.constants import DEFAULT_MAX_BOOKINGS_PER_DAY
from src.locales import get_text


def validate_booking_time(workout_datetime: datetime, lang: str = 'ru') -> tuple[bool, str]:
    """
    Валидация времени записи на тренировку.
    Запись возможна только на Сегодня (после текущего времени) и Завтра.
    
    Returns:
        tuple[bool, str]: (валидно, сообщение об ошибке)
    """
    now = datetime.now()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    workout_date = workout_datetime.date()
    
    # Проверка что тренировка не в прошлом
    if workout_datetime < now:
        return False, get_text('booking.past_workout', lang)

    return True, ""


def can_book_workout(
    bookings_count: int,
    max_bookings_per_day: int = DEFAULT_MAX_BOOKINGS_PER_DAY,
    lang: str = 'ru'
) -> tuple[bool, str]:
    """
    Проверка, может ли пользователь записаться на тренировку.
    Лимит записей в день задаётся в настройках (дефолт в constants).
    
    Returns:
        tuple[bool, str]: (можно записаться, сообщение об ошибке)
    """
    if bookings_count >= max_bookings_per_day:
        return False, get_text('booking.limit_exceeded', lang, max=max_bookings_per_day)
    
    return True, ""


def validate_workout_slot(
    current_participants: int,
    max_participants: int,
    lang: str = 'ru'
) -> tuple[bool, str]:
    """
    Проверка наличия свободных мест на тренировке.
    
    Returns:
        tuple[bool, str]: (есть места, сообщение об ошибке)
    """
    if current_participants >= max_participants:
        return False, get_text('booking.no_free_slots', lang, max=max_participants)
    
    return True, ""
