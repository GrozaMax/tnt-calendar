"""
Базовые обработчики команд
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from src.utils.decorators import ensure_user_exists
from src.handlers.athlete import show_main_menu, show_help

logger = logging.getLogger(__name__)


@ensure_user_exists
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await show_main_menu(update, context)


@ensure_user_exists
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await show_help(update, context)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f'Update {update} caused error {context.error}', exc_info=context.error)
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Произошла ошибка при обработке вашего запроса. "
            "Пожалуйста, попробуйте позже."
        )

