"""
Inline-клавиатуры для тренеров
"""
from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from src.locales import get_text
from src.keyboards.athlete_keyboards import format_dt


def trainer_section_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Инлайн-меню 'Тренерская': обзор расписания, мои тренировки, слоты"""
    keyboard = [
        [InlineKeyboardButton(get_text('trainer.schedule_overview', lang), callback_data='schedule')],
        [InlineKeyboardButton(get_text('trainer.my_workouts_btn', lang), callback_data='trainer_workouts:week')],
        [InlineKeyboardButton(get_text('trainer.free_slots_btn', lang), callback_data='trainer_free_slots')],
        [InlineKeyboardButton(get_text('menu.back', lang), callback_data='main_menu')],
    ]
    return InlineKeyboardMarkup(keyboard)


def trainer_workouts_list_keyboard(workouts: List, lang: str = 'ru') -> InlineKeyboardMarkup:
    """Список тренировок тренера"""
    keyboard = []
    if workouts:
        for workout in workouts[:20]:
            occupancy = workout.current_participants / workout.max_participants
            status = "🔴" if occupancy >= 1.0 else ("🟡" if occupancy >= 0.8 else "🟢")
            button_text = (
                f"{status} {format_dt(workout.datetime, '%d.%m %H:%M', lang)} - {workout.name} "
                f"({workout.current_participants}/{workout.max_participants})"
            )
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f'trainer_workout_info:{workout.id}')])
    keyboard.append([InlineKeyboardButton(get_text('menu.back', lang), callback_data='trainer_menu')])
    return InlineKeyboardMarkup(keyboard)


def trainer_workout_details_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Просмотр деталей тренировки тренером"""
    keyboard = [[InlineKeyboardButton(get_text('menu.back', lang), callback_data='trainer_menu')]]
    return InlineKeyboardMarkup(keyboard)


def trainer_free_slots_keyboard(workouts: List, lang: str = 'ru') -> InlineKeyboardMarkup:
    """Свободные слоты для тренеров"""
    keyboard = []
    if workouts:
        for workout in workouts[:20]:
            button_text = f"{format_dt(workout.datetime, '%d.%m %H:%M', lang)} - {workout.name} ({workout.current_participants}/{workout.max_participants})"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f'trainer_assign:{workout.id}')])
    keyboard.append([InlineKeyboardButton(get_text('menu.back', lang), callback_data='trainer_menu')])
    return InlineKeyboardMarkup(keyboard)


def trainer_assigned_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Клавиатура после назначения себя на тренировку"""
    keyboard = [
        [InlineKeyboardButton("📋 Свободные слоты", callback_data='trainer_free_slots')],
        [InlineKeyboardButton(get_text('menu.back', lang), callback_data='trainer_menu')],
    ]
    return InlineKeyboardMarkup(keyboard)
