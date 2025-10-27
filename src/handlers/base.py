"""
Базовые обработчики команд
"""
from telegram import Update
from telegram.ext import ContextTypes


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        f"Я бот TNT Calendar. Я помогу тебе управлять твоим календарем.\n\n"
        f"Доступные команды:\n"
        f"/start - Начать работу с ботом\n"
        f"/help - Показать справку\n"
        f"/calendar - Открыть календарь"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "📋 *Справка по командам:*\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/calendar - Открыть календарь\n\n"
        "Для получения дополнительной информации свяжитесь с администратором."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /calendar"""
    await update.message.reply_text(
        "📅 Календарь в разработке...\n"
        "Скоро здесь появится функционал работы с календарем!"
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    print(f'Update {update} caused error {context.error}')
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла ошибка при обработке вашего запроса. "
            "Пожалуйста, попробуйте позже."
        )

