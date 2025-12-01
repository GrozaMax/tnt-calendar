"""
Inline-клавиатуры для атлета
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List

from src.models import Workout
from src.locales import get_text


def main_menu_keyboard(lang: str = 'ru', is_admin: bool = False) -> InlineKeyboardMarkup:
    """Главное меню атлета"""
    keyboard = [
        [InlineKeyboardButton(
            get_text('menu.schedule', lang),
            callback_data='schedule'
        )],
        [InlineKeyboardButton(
            get_text('menu.my_bookings', lang),
            callback_data='my_bookings'
        )],
        [InlineKeyboardButton(
            get_text('menu.settings', lang),
            callback_data='settings'
        )],
        [InlineKeyboardButton(
            get_text('menu.help', lang),
            callback_data='help'
        )]
    ]
    
    # Добавляем кнопку админ-панели для админов
    if is_admin:
        keyboard.insert(2, [InlineKeyboardButton(
            "👑 Админ-панель",
            callback_data='admin_menu'
        )])
    
    return InlineKeyboardMarkup(keyboard)


def schedule_days_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Выбор дня для просмотра расписания"""
    keyboard = [
        [InlineKeyboardButton(
            get_text('schedule.today', lang),
            callback_data='schedule:today'
        )],
        [InlineKeyboardButton(
            get_text('schedule.tomorrow', lang),
            callback_data='schedule:tomorrow'
        )],
        [InlineKeyboardButton(
            get_text('menu.back', lang),
            callback_data='main_menu'
        )]
    ]
    return InlineKeyboardMarkup(keyboard)


def workouts_list_keyboard(
    workouts: List[Workout],
    lang: str = 'ru'
) -> InlineKeyboardMarkup:
    """
    Список тренировок на выбранный день.
    
    Args:
        workouts: Список тренировок
        lang: Язык интерфейса
    """
    keyboard = []
    
    for workout in workouts:
        # Форматирование времени и информации о тренировке
        time_str = workout.datetime.strftime('%H:%M')
        participants = f"{workout.current_participants}/{workout.max_participants}"
        
        # Эмодзи в зависимости от заполненности
        if workout.is_full:
            emoji = "❌"
        elif workout.current_participants > workout.max_participants * 0.7:
            emoji = "⚠️"
        else:
            emoji = "✅"
        
        button_text = f"{emoji} {time_str} | {workout.name} ({participants})"
        
        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f'workout_info:{workout.id}'
            )
        ])
    
    # Кнопка "Назад"
    keyboard.append([
        InlineKeyboardButton(
            get_text('menu.back', lang),
            callback_data='schedule'
        )
    ])
    
    return InlineKeyboardMarkup(keyboard)


def workout_actions_keyboard(
    workout_id: int,
    is_booked: bool = False,
    is_full: bool = False,
    lang: str = 'ru'
) -> InlineKeyboardMarkup:
    """
    Действия с тренировкой (запись/отмена).
    
    Args:
        workout_id: ID тренировки
        is_booked: Уже записан ли пользователь
        is_full: Заполнена ли тренировка
        lang: Язык интерфейса
    """
    keyboard = []
    
    if is_booked:
        # Кнопка отмены записи
        keyboard.append([
            InlineKeyboardButton(
                get_text('booking.button_cancel', lang),
                callback_data=f'cancel_booking:{workout_id}'
            )
        ])
    elif not is_full:
        # Кнопка записи
        keyboard.append([
            InlineKeyboardButton(
                get_text('booking.button_book', lang),
                callback_data=f'book:{workout_id}'
            )
        ])
    
    # Кнопка "Назад"
    keyboard.append([
        InlineKeyboardButton(
            get_text('menu.back', lang),
            callback_data='schedule:back'
        )
    ])
    
    return InlineKeyboardMarkup(keyboard)


def my_bookings_keyboard(
    bookings: List,
    lang: str = 'ru'
) -> InlineKeyboardMarkup:
    """
    Список записей пользователя.
    
    Args:
        bookings: Список записей (Booking objects)
        lang: Язык интерфейса
    """
    keyboard = []
    
    for booking in bookings:
        workout = booking.workout
        time_str = workout.datetime.strftime('%d.%m %H:%M')
        button_text = f"📋 {time_str} | {workout.name}"
        
        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f'booking_info:{booking.id}'
            )
        ])
    
    # Кнопка "Назад"
    keyboard.append([
        InlineKeyboardButton(
            get_text('menu.back', lang),
            callback_data='main_menu'
        )
    ])
    
    return InlineKeyboardMarkup(keyboard)


def booking_info_keyboard(
    booking_id: int,
    lang: str = 'ru'
) -> InlineKeyboardMarkup:
    """Действия с конкретной записью"""
    keyboard = [
        [InlineKeyboardButton(
            get_text('booking.button_cancel', lang),
            callback_data=f'cancel_booking_from_list:{booking_id}'
        )],
        [InlineKeyboardButton(
            get_text('menu.back', lang),
            callback_data='my_bookings'
        )]
    ]
    return InlineKeyboardMarkup(keyboard)


def back_to_main_menu_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Простая клавиатура с кнопкой возврата в главное меню"""
    keyboard = [[
        InlineKeyboardButton(
            get_text('menu.back', lang),
            callback_data='main_menu'
        )
    ]]
    return InlineKeyboardMarkup(keyboard)


def settings_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Меню настроек"""
    keyboard = [
        [InlineKeyboardButton(
            "🌐 Язык / Language",
            callback_data='change_language'
        )],
        [InlineKeyboardButton(
            get_text('menu.back', lang),
            callback_data='main_menu'
        )]
    ]
    return InlineKeyboardMarkup(keyboard)


def language_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка"""
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data='set_lang:ru')],
        [InlineKeyboardButton("🇺🇦 Українська", callback_data='set_lang:ua')],
        [InlineKeyboardButton("🇬🇧 English", callback_data='set_lang:en')],
        [InlineKeyboardButton("🇩🇪 Deutsch", callback_data='set_lang:de')],
        [InlineKeyboardButton("🇬🇪 ქართული", callback_data='set_lang:ge')],
        [InlineKeyboardButton("◀️ Назад / Back", callback_data='settings')]
    ]
    return InlineKeyboardMarkup(keyboard)

