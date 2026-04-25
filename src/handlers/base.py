"""
Базовые обработчики команд
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from src.utils.decorators import ensure_user_exists
from src.handlers.athlete import show_main_menu, show_help
from src.keyboards.athlete_keyboards import (
    main_reply_keyboard, schedule_days_keyboard,
    my_bookings_keyboard, back_to_main_menu_keyboard,
    REPLY_BOOK_WORKOUT_TEXTS, REPLY_MY_BOOKINGS_TEXTS,
    REPLY_TRAINER_SECTION_TEXTS, REPLY_ADMIN_PANEL_TEXTS,
)
from src.keyboards.trainer_keyboards import trainer_section_keyboard
from src.locales import get_text

logger = logging.getLogger(__name__)


def _user_role_str(user) -> str:
    if not user:
        return 'athlete'
    return user.ui_role_key()


@ensure_user_exists
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    role = _user_role_str(user)
    # Устанавливаем нижнюю клавиатуру (сообщение не удаляем — иначе клавиатура исчезнет)
    await update.message.reply_text("⌨️", reply_markup=main_reply_keyboard(lang, role))
    # Главное меню; show_main_menu сохранит nav_message_id
    await show_main_menu(update, context)
    context.user_data['current_screen'] = None  # сбрасываем, чтобы повторный /start работал


@ensure_user_exists
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await show_help(update, context)


async def _nav_edit_or_send(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            text: str, reply_markup, parse_mode: str = None):
    """Редактирует сохранённое навигационное сообщение или отправляет новое."""
    chat_id = update.effective_chat.id
    nav_id = context.user_data.get('nav_message_id')
    kwargs = {'text': text, 'reply_markup': reply_markup}
    if parse_mode:
        kwargs['parse_mode'] = parse_mode

    if nav_id:
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=nav_id, **kwargs)
            return
        except Exception:
            pass  # сообщение слишком старое или уже изменено — отправим новое

    sent = await update.message.reply_text(**kwargs)
    context.user_data['nav_message_id'] = sent.message_id


@ensure_user_exists
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Единый обработчик текстовых сообщений: нижняя панель навигации + причина удаления тренировки"""
    if not update.message:
        return  # edited_message — игнорируем
    text = update.message.text
    user = context.user_data.get('current_user')
    lang = user.language if user else 'ru'

    _ALL_NAV = REPLY_BOOK_WORKOUT_TEXTS | REPLY_MY_BOOKINGS_TEXTS | REPLY_TRAINER_SECTION_TEXTS | REPLY_ADMIN_PANEL_TEXTS | REPLY_SETTINGS_TEXTS

    # Если это нажатие кнопки нижней панели — удаляем сообщение пользователя
    if text in _ALL_NAV:
        try:
            await update.message.delete()
        except Exception:
            pass

    current_screen = context.user_data.get('current_screen')

    if text in REPLY_BOOK_WORKOUT_TEXTS:
        # Атлет: "Записаться" — выбор дня
        if current_screen == 'schedule':
            return
        keyboard = schedule_days_keyboard(lang)
        await _nav_edit_or_send(update, context, get_text('schedule.select_day', lang), keyboard)
        context.user_data['current_screen'] = 'schedule'

    elif text in REPLY_MY_BOOKINGS_TEXTS:
        if current_screen == 'bookings':
            return
        from src.database import get_session
        from src.services.booking_service import BookingService

        async with get_session() as session:
            booking_service = BookingService(session)
            bookings = await booking_service.get_user_active_bookings(user.id)

        if not bookings:
            await _nav_edit_or_send(
                update, context,
                get_text('my_bookings.no_bookings', lang),
                back_to_main_menu_keyboard(lang),
            )
        else:
            text_msg = get_text('my_bookings.title', lang) + "\n\n"
            text_msg += get_text('my_bookings.upcoming', lang)
            await _nav_edit_or_send(update, context, text_msg, my_bookings_keyboard(bookings, lang))
        context.user_data['current_screen'] = 'bookings'

    elif text in REPLY_TRAINER_SECTION_TEXTS:
        # Тренер/Админ: "Тренерская" — всегда возвращаем на стартовое меню раздела
        title = get_text('trainer.section_title', lang)
        kb = trainer_section_keyboard(lang)
        await _nav_edit_or_send(update, context, f"*{title}*\n\n{get_text('trainer.select_section', lang)}", kb, parse_mode='Markdown')
        context.user_data['current_screen'] = 'trainer_section'

    elif text in REPLY_ADMIN_PANEL_TEXTS:
        # Админ: "Админ панель" — всегда возвращаем на стартовое меню раздела
        from src.handlers.admin import _build_admin_menu_content
        admin_text, admin_kb = _build_admin_menu_content(lang)
        await _nav_edit_or_send(update, context, admin_text, admin_kb, parse_mode='Markdown')
        context.user_data['current_screen'] = 'admin_menu'

    elif text in REPLY_SETTINGS_TEXTS:
        from src.handlers.athlete import show_settings
        await show_settings(update, context, skip_answer=True)

    elif context.user_data.get('pending_delete_workout_id'):
        # Режим ввода причины удаления тренировки (для администратора)
        from src.handlers.admin import handle_admin_delete_reason
        await handle_admin_delete_reason(update, context)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f'Update {update} caused error {context.error}', exc_info=context.error)
    
    if update and update.effective_message:
        # Здесь нет context.user_data если произошла ошибка до загрузки пользователя, так что используем fallback
        from src.locales import get_text
        lang = 'ru'
        if hasattr(context, 'user_data') and context.user_data and 'current_user' in context.user_data:
            user = context.user_data.get('current_user')
            if user and 'language' in user.__dict__:
                lang = user.__dict__['language'] or 'ru'
        
        await update.effective_message.reply_text(get_text('common.error_processing', lang))
