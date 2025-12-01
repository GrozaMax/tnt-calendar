"""
Inline-клавиатуры для администратора
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List

from src.models import Workout, User
from src.locales import get_text


def admin_main_menu_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Главное меню администратора"""
    keyboard = [
        [InlineKeyboardButton(
            "📅 Создать расписание",
            callback_data='admin_create_schedule'
        )],
        [InlineKeyboardButton(
            "📋 Управление тренировками",
            callback_data='admin_manage_workouts'
        )],
        [InlineKeyboardButton(
            "👥 Управление пользователями",
            callback_data='admin_manage_users'
        )],
        [InlineKeyboardButton(
            get_text('menu.back', lang),
            callback_data='main_menu'
        )]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_schedule_options_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Выбор количества недель для создания расписания"""
    keyboard = [
        [InlineKeyboardButton("📅 1 неделя", callback_data='create_schedule:1')],
        [InlineKeyboardButton("📅 2 недели", callback_data='create_schedule:2')],
        [InlineKeyboardButton("📅 4 недели", callback_data='create_schedule:4')],
        [InlineKeyboardButton("📅 8 недель", callback_data='create_schedule:8')],
        [InlineKeyboardButton("📅 12 недель (3 месяца)", callback_data='create_schedule:12')],
        [InlineKeyboardButton(
            get_text('menu.back', lang),
            callback_data='admin_menu'
        )]
    ]
    return InlineKeyboardMarkup(keyboard)


def manage_workouts_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Меню управления тренировками"""
    keyboard = [
        [InlineKeyboardButton(
            "📋 Все тренировки",
            callback_data='admin_list_workouts'
        )],
        [InlineKeyboardButton(
            "🗑️ Удалить тренировку",
            callback_data='admin_delete_workout'
        )],
        [InlineKeyboardButton(
            get_text('menu.back', lang),
            callback_data='admin_menu'
        )]
    ]
    return InlineKeyboardMarkup(keyboard)


def workouts_date_selection_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Выбор даты для просмотра тренировок"""
    keyboard = [
        [InlineKeyboardButton(
            "Сегодня",
            callback_data='admin_workouts_date:today'
        )],
        [InlineKeyboardButton(
            "Завтра",
            callback_data='admin_workouts_date:tomorrow'
        )],
        [InlineKeyboardButton(
            "Эта неделя",
            callback_data='admin_workouts_date:week'
        )],
        [InlineKeyboardButton(
            get_text('menu.back', lang),
            callback_data='admin_manage_workouts'
        )]
    ]
    return InlineKeyboardMarkup(keyboard)


def workout_actions_keyboard(
    workout_id: int,
    lang: str = 'ru'
) -> InlineKeyboardMarkup:
    """Действия с тренировкой для админа"""
    keyboard = [
        [InlineKeyboardButton(
            "👥 Список участников",
            callback_data=f'admin_workout_participants:{workout_id}'
        )],
        [InlineKeyboardButton(
            "🗑️ Удалить тренировку",
            callback_data=f'admin_confirm_delete:{workout_id}'
        )],
        [InlineKeyboardButton(
            get_text('menu.back', lang),
            callback_data='admin_list_workouts'
        )]
    ]
    return InlineKeyboardMarkup(keyboard)


def confirm_delete_keyboard(
    workout_id: int,
    lang: str = 'ru'
) -> InlineKeyboardMarkup:
    """Подтверждение удаления тренировки"""
    keyboard = [
        [InlineKeyboardButton(
            "✅ Да, удалить",
            callback_data=f'admin_delete_confirmed:{workout_id}'
        )],
        [InlineKeyboardButton(
            "❌ Отмена",
            callback_data=f'admin_workout_info:{workout_id}'
        )]
    ]
    return InlineKeyboardMarkup(keyboard)


def manage_users_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Меню управления пользователями"""
    keyboard = [
        [InlineKeyboardButton(
            "👥 Список всех пользователей",
            callback_data='admin_list_users'
        )],
        [InlineKeyboardButton(
            "🎓 Назначить тренера",
            callback_data='admin_promote_trainer'
        )],
        [InlineKeyboardButton(
            get_text('menu.back', lang),
            callback_data='admin_menu'
        )]
    ]
    return InlineKeyboardMarkup(keyboard)


def users_list_keyboard(
    users: List[User],
    lang: str = 'ru'
) -> InlineKeyboardMarkup:
    """Список пользователей с действиями"""
    keyboard = []
    
    for user in users[:20]:  # Ограничение в 20 пользователей на страницу
        role_emoji = {
            "athlete": "🏋️",
            "trainer": "🤸‍♀️",
            "admin": "👑"
        }.get(user.role.value, "👤")
        
        button_text = f"{role_emoji} {user.full_name} ({user.role.value})"
        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f'admin_user_info:{user.id}'
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            get_text('menu.back', lang),
            callback_data='admin_manage_users'
        )
    ])
    
    return InlineKeyboardMarkup(keyboard)


def user_actions_keyboard(
    user_id: int,
    current_role: str,
    lang: str = 'ru'
) -> InlineKeyboardMarkup:
    """Действия с пользователем"""
    keyboard = []
    
    if current_role == "athlete":
        keyboard.append([
            InlineKeyboardButton(
                "🎓 Назначить тренером",
                callback_data=f'admin_set_role:{user_id}:trainer'
            )
        ])
    elif current_role == "trainer":
        keyboard.append([
            InlineKeyboardButton(
                "⬇️ Снять роль тренера",
                callback_data=f'admin_set_role:{user_id}:athlete'
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            get_text('menu.back', lang),
            callback_data='admin_list_users'
        )
    ])
    
    return InlineKeyboardMarkup(keyboard)


def back_to_admin_menu_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Кнопка возврата в админ-меню"""
    keyboard = [[
        InlineKeyboardButton(
            "◀️ В админ-меню",
            callback_data='admin_menu'
        )
    ]]
    return InlineKeyboardMarkup(keyboard)

