"""
Inline-клавиатуры для атлета
"""
from datetime import date, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from typing import List

from src.models import Workout
from src.locales import get_text

_LANGS = ('ru', 'en', 'ua', 'de', 'ge')

# Наборы всех возможных текстов кнопок (для любого языка) — используются в handle_text_message
REPLY_BOOK_WORKOUT_TEXTS    = frozenset(get_text('reply_kb.book_workout',    l) for l in _LANGS)
REPLY_MY_BOOKINGS_TEXTS     = frozenset(get_text('reply_kb.my_bookings',     l) for l in _LANGS)
REPLY_SCHEDULE_TEXTS        = frozenset(get_text('reply_kb.schedule',        l) for l in _LANGS)
REPLY_MY_WORKOUTS_TEXTS     = frozenset(get_text('reply_kb.my_workouts',     l) for l in _LANGS)
REPLY_SETTINGS_TEXTS        = frozenset(get_text('menu.settings',            l) for l in _LANGS)
REPLY_HELP_TEXTS            = frozenset(get_text('menu.help',                l) for l in _LANGS)
REPLY_TRAINER_SECTION_TEXTS = frozenset(get_text('reply_kb.trainer_section', l) for l in _LANGS)
REPLY_ADMIN_PANEL_TEXTS     = frozenset(get_text('reply_kb.admin_panel',     l) for l in _LANGS)

WEEKDAY_NAMES = {
    'ru': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
    'en': ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'],
    'ua': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд'],
    'de': ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'],
    'ge': ['ორშ', 'სამ', 'ოთხ', 'ხუთ', 'პარ', 'შაბ', 'კვი'],
}


def format_dt(dt, fmt: str = '%d.%m.%Y %H:%M', lang: str = 'ru') -> str:
    """Format a datetime/date with a localized weekday prefix.

    Examples:
        format_dt(dt, '%d.%m.%Y %H:%M', 'ru')  ->  'Пн 20.04.2026 10:00'
        format_dt(dt, '%d.%m %H:%M', 'en')      ->  'Mo 20.04 10:00'
        format_dt(dt, '%d.%m.%Y', 'ru')          ->  'Пн 20.04.2026'
    """
    day_names = WEEKDAY_NAMES.get(lang, WEEKDAY_NAMES['ru'])
    weekday = day_names[dt.weekday()]
    return f"{weekday} {dt.strftime(fmt)}"


def main_reply_keyboard(lang: str = 'ru', role: str = 'athlete') -> ReplyKeyboardMarkup:
    """Постоянная нижняя клавиатура (под полем ввода текста), зависит от роли и языка"""
    start_btn = KeyboardButton("/start")
    settings_btn = KeyboardButton(get_text('menu.settings', lang))
    if role == 'admin':
        keyboard = [
            [KeyboardButton(get_text('reply_kb.trainer_section', lang)),
             KeyboardButton(get_text('reply_kb.admin_panel', lang))],
            [settings_btn],
            [start_btn],
        ]
    elif role == 'trainer':
        keyboard = [
            [KeyboardButton(get_text('reply_kb.trainer_section', lang))],
            [settings_btn],
            [start_btn],
        ]
    else:  # athlete
        keyboard = [
            [KeyboardButton(get_text('reply_kb.book_workout', lang))],
            [KeyboardButton(get_text('reply_kb.my_bookings', lang))],
            [settings_btn],
            [start_btn],
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)


def back_to_schedule_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Простая кнопка Назад к расписанию"""
    keyboard = [[InlineKeyboardButton(get_text('menu.back', lang), callback_data='schedule:back')]]
    return InlineKeyboardMarkup(keyboard)


def main_menu_keyboard(lang: str = 'ru', is_admin: bool = False, is_trainer: bool = False) -> InlineKeyboardMarkup:
    """Главное меню — зависит от роли пользователя"""
    if is_admin:
        keyboard = [
            [InlineKeyboardButton(get_text('reply_kb.trainer_section', lang), callback_data='trainer_menu')],
            [InlineKeyboardButton(get_text('reply_kb.admin_panel', lang), callback_data='admin_menu')],
            [InlineKeyboardButton(get_text('menu.help', lang), callback_data='help')],
        ]
    elif is_trainer:
        keyboard = [
            [InlineKeyboardButton(get_text('reply_kb.trainer_section', lang), callback_data='trainer_menu')],
            [InlineKeyboardButton(get_text('menu.help', lang), callback_data='help')],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(get_text('reply_kb.book_workout', lang), callback_data='schedule')],
            [InlineKeyboardButton(get_text('reply_kb.my_bookings', lang), callback_data='my_bookings')],
            [InlineKeyboardButton(get_text('menu.help', lang), callback_data='help')],
        ]
    return InlineKeyboardMarkup(keyboard)


def schedule_days_keyboard(lang: str = 'ru', back_callback: str = 'main_menu') -> InlineKeyboardMarkup:
    """Выбор дня — показывает текущую неделю (7 дней от сегодня)"""
    today = date.today()
    day_names = WEEKDAY_NAMES.get(lang, WEEKDAY_NAMES['ru'])
    keyboard = []
    for i in range(7):
        d = today + timedelta(days=i)
        label = f"{day_names[d.weekday()]} {d.strftime('%d.%m')}"
        if i == 0:
            label = f"📍 {label}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f'schedule:{d.isoformat()}')])
    keyboard.append([InlineKeyboardButton(get_text('reply_kb.schedule_image', lang), callback_data='schedule_image')])
    keyboard.append([InlineKeyboardButton(get_text('menu.back', lang), callback_data=back_callback)])
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
        # Кнопки записи
        keyboard.append([
            InlineKeyboardButton(
                get_text('booking.button_book', lang),
                callback_data=f'book:{workout_id}'
            ),
            InlineKeyboardButton(
                get_text('booking.button_book', lang) + " +1",
                callback_data=f'book_plus_one:{workout_id}'
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
        time_str = format_dt(workout.datetime, '%d.%m %H:%M', lang)
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


def settings_keyboard(lang: str = 'ru', notifications_enabled: bool = True, reminder_minutes: int = 60) -> InlineKeyboardMarkup:
    """Меню настроек"""
    notif_btn = (
        get_text('settings.btn_disable_notifications', lang)
        if notifications_enabled
        else get_text('settings.btn_enable_notifications', lang)
    )
    
    remind_text = get_text('settings.btn_reminder_time', lang, minutes=reminder_minutes)
    
    keyboard = [
        [InlineKeyboardButton(
            notif_btn,
            callback_data='toggle_notifications'
        )]
    ]
    
    if notifications_enabled:
        keyboard.append([InlineKeyboardButton(
            remind_text,
            callback_data='toggle_reminder_time'
        )])
        
    keyboard.extend([
        [InlineKeyboardButton(
            "🌐 Язык / Language",
            callback_data='change_language'
        )],
        [InlineKeyboardButton(
            get_text('menu.back', lang),
            callback_data='main_menu'
        )]
    ])
    return InlineKeyboardMarkup(keyboard)


def language_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка"""
    keyboard = [
        [InlineKeyboardButton("🇬🇪 ქართული", callback_data='set_lang:ge')],
        [InlineKeyboardButton("🇬🇧 English", callback_data='set_lang:en')],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data='set_lang:ru')],
        [InlineKeyboardButton("🇺🇦 Українська", callback_data='set_lang:ua')],
        [InlineKeyboardButton("🇩🇪 Deutsch", callback_data='set_lang:de')],
        [InlineKeyboardButton(get_text('common.back_back', lang), callback_data='settings')]
    ]
    return InlineKeyboardMarkup(keyboard)

