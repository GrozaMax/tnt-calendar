"""
Inline-клавиатуры для администратора
"""
from datetime import date, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List

from src.locales import get_text
from src.keyboards.athlete_keyboards import WEEKDAY_NAMES, format_dt


def admin_main_menu_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Главное меню администратора"""
    keyboard = [
        [InlineKeyboardButton(get_text('admin.schedule_today', lang), callback_data='admin_view_workouts:today')],
        [InlineKeyboardButton(get_text('admin.schedule_tomorrow', lang), callback_data='admin_view_workouts:tomorrow')],
        [InlineKeyboardButton(get_text('admin.schedule_week', lang), callback_data='admin_view_workouts:week')],
        [InlineKeyboardButton(get_text('admin.users_stats', lang), callback_data='admin_users_stats')],
        [InlineKeyboardButton(get_text('admin.schedule_image', lang), callback_data='admin_schedule_image')],
        [InlineKeyboardButton(get_text('menu.back', lang), callback_data='main_menu')],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_week_selection_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Выбор дня недели для просмотра расписания"""
    today = date.today()
    day_names = WEEKDAY_NAMES.get(lang, WEEKDAY_NAMES['ru'])
    keyboard = []
    for i in range(7):
        d = today + timedelta(days=i)
        label = f"{'📍 ' if i == 0 else ''}{day_names[d.weekday()]} {d.strftime('%d.%m')}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f'admin_day:{d.isoformat()}')])
    keyboard.append([InlineKeyboardButton(get_text('menu.back', lang), callback_data='admin_menu')])
    return InlineKeyboardMarkup(keyboard)


def admin_workouts_list_keyboard(workouts: List, period: str, lang: str = 'ru') -> InlineKeyboardMarkup:
    """Список тренировок (сегодня/завтра)"""
    keyboard = []
    for workout in workouts[:20]:
        occupancy = workout.current_participants / workout.max_participants
        status = "🔴" if occupancy >= 1.0 else ("🟡" if occupancy >= 0.8 else "🟢")
        button_text = (
            f"{status} {format_dt(workout.datetime, '%d.%m %H:%M', lang)} - {workout.name} "
            f"({workout.current_participants}/{workout.max_participants})"
        )
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'admin_workout_details:{workout.id}:{period}')])
    keyboard.append([InlineKeyboardButton(get_text('menu.back', lang), callback_data='admin_menu')])
    return InlineKeyboardMarkup(keyboard)


def admin_day_workouts_list_keyboard(workouts: List, day_str: str, lang: str = 'ru') -> InlineKeyboardMarkup:
    """Список тренировок за конкретный день (из недели)"""
    keyboard = []
    for workout in workouts:
        occupancy = workout.current_participants / workout.max_participants
        status = "🔴" if occupancy >= 1.0 else ("🟡" if occupancy >= 0.8 else "🟢")
        button_text = (
            f"{status} {workout.datetime.strftime('%H:%M')} {workout.name} "
            f"({workout.current_participants}/{workout.max_participants})"
        )
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'admin_workout_details:{workout.id}:{day_str}')])
    keyboard.append([InlineKeyboardButton(get_text('admin.back_to_week', lang), callback_data='admin_view_workouts:week')])
    return InlineKeyboardMarkup(keyboard)


def admin_workout_details_keyboard(workout_id: int, source: str, lang: str = 'ru') -> InlineKeyboardMarkup:
    """Действия с тренировкой (детали)"""
    if source in ('today', 'tomorrow'):
        back_callback = f'admin_view_workouts:{source}'
    else:
        back_callback = f'admin_day:{source}'
        
    keyboard = [
        [
            InlineKeyboardButton(get_text('admin.assign_trainer', lang), callback_data=f'admin_select_trainer:{workout_id}:{source}'),
            InlineKeyboardButton(get_text('admin.delete_workout', lang), callback_data=f'admin_delete_workout_confirm:{workout_id}'),
        ],
        [InlineKeyboardButton(get_text('menu.back', lang), callback_data=back_callback)]
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_users_stats_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Клавиатура для статистики пользователей"""
    keyboard = [[InlineKeyboardButton(get_text('menu.back', lang), callback_data='admin_menu')]]
    return InlineKeyboardMarkup(keyboard)


def admin_delete_workout_confirm_keyboard(workout_id: int, lang: str = 'ru') -> InlineKeyboardMarkup:
    """Подтверждение удаления тренировки"""
    keyboard = [[InlineKeyboardButton(get_text('admin.delete_cancel', lang), callback_data=f'admin_cancel_delete:{workout_id}')]]
    return InlineKeyboardMarkup(keyboard)


def admin_select_trainer_keyboard(trainers: List, workout_id: int, source: str, lang: str = 'ru') -> InlineKeyboardMarkup:
    """Выбор тренера для назначения"""
    from src.models import UserRole
    keyboard = []
    for t in trainers:
        role_label = " 👑" if t.role == UserRole.ADMIN else ""
        keyboard.append([
            InlineKeyboardButton(
                f"{t.full_name}{role_label}",
                callback_data=f'admin_assign_trainer:{workout_id}:{t.id}:{source}'
            )
        ])
    keyboard.append([InlineKeyboardButton(get_text('admin.no_trainer_btn', lang), callback_data=f'admin_assign_trainer:{workout_id}:0:{source}')])
    keyboard.append([InlineKeyboardButton(get_text('menu.back', lang), callback_data=f'admin_workout_details:{workout_id}:{source}')])
    return InlineKeyboardMarkup(keyboard)


def admin_trainer_assigned_keyboard(workout_id: int, source: str, lang: str = 'ru') -> InlineKeyboardMarkup:
    """Клавиатура после назначения тренера"""
    keyboard = [[InlineKeyboardButton(get_text('admin.to_workout', lang), callback_data=f'admin_workout_details:{workout_id}:{source}')]]
    return InlineKeyboardMarkup(keyboard)


def admin_schedule_image_menu_keyboard(image_exists: bool, lang: str = 'ru') -> InlineKeyboardMarkup:
    """Меню управления картинкой расписания"""
    keyboard = [
        [InlineKeyboardButton(get_text('admin.image_upload_btn', lang), callback_data='admin_upload_schedule_image')],
    ]
    if image_exists:
        keyboard.append([InlineKeyboardButton(get_text('admin.image_delete_btn', lang), callback_data='admin_delete_schedule_image')])
    keyboard.append([InlineKeyboardButton(get_text('menu.back', lang), callback_data='admin_menu')])
    return InlineKeyboardMarkup(keyboard)


def admin_upload_schedule_image_prompt_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Отмена загрузки картинки"""
    keyboard = [
        [InlineKeyboardButton(get_text('admin.image_cancel', lang), callback_data='admin_schedule_image')]
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_delete_schedule_image_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Возврат после удаления картинки"""
    keyboard = [
        [InlineKeyboardButton(get_text('menu.back', lang), callback_data='admin_schedule_image')]
    ]
    return InlineKeyboardMarkup(keyboard)
