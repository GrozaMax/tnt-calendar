"""
Главный модуль бота
"""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler

from src.config import Config
from src.handlers.base import (
    start_command,
    help_command,
    calendar_command,
    error_handler
)


# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, Config.LOG_LEVEL)
)
logger = logging.getLogger(__name__)


class TelegramBot:
    """Класс Telegram бота"""
    
    def __init__(self):
        """Инициализация бота"""
        Config.validate()
        self.application = Application.builder().token(Config.BOT_TOKEN).build()
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрация обработчиков команд"""
        # Команды
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("help", help_command))
        self.application.add_handler(CommandHandler("calendar", calendar_command))
        
        # Обработчик ошибок
        self.application.add_error_handler(error_handler)
        
        logger.info("Обработчики команд зарегистрированы")
    
    def run(self):
        """Запуск бота"""
        logger.info("Запуск бота...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("Бот остановлен")


if __name__ == '__main__':
    bot = TelegramBot()
    bot.run()

