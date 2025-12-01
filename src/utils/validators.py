"""
Валидаторы для бизнес-логики
"""
from datetime import datetime, date, timedelta


def validate_booking_time(workout_datetime: datetime) -> tuple[bool, str]:
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
        return False, "❌ Нельзя записаться на тренировку в прошлом"
    
    # Проверка что тренировка сегодня или завтра
    if workout_date not in [today, tomorrow]:
        return False, "❌ Запись возможна только на сегодня или завтра"
    
    return True, ""


def can_book_workout(
    bookings_count: int,
    max_bookings_per_day: int = 2
) -> tuple[bool, str]:
    """
    Проверка, может ли пользователь записаться на тренировку.
    Максимум 2 записи в день.
    
    Returns:
        tuple[bool, str]: (можно записаться, сообщение об ошибке)
    """
    if bookings_count >= max_bookings_per_day:
        return False, f"❌ Вы уже записаны на {max_bookings_per_day} тренировки в этот день"
    
    return True, ""


def validate_workout_slot(
    current_participants: int,
    max_participants: int
) -> tuple[bool, str]:
    """
    Проверка наличия свободных мест на тренировке.
    
    Returns:
        tuple[bool, str]: (есть места, сообщение об ошибке)
    """
    if current_participants >= max_participants:
        return False, "❌ На этой тренировке нет свободных мест"
    
    return True, ""

