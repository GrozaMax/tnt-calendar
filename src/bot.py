"""
Главный модуль бота
"""
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler
)

from src.config import Config
from src.database import init_db
from src.handlers.base import (
    start_command,
    help_command,
    error_handler
)
from src.handlers.athlete import (
    show_main_menu,
    show_schedule_menu,
    show_schedule_for_day,
    show_workout_info,
    book_workout,
    cancel_booking_from_workout,
    show_my_bookings,
    show_booking_info,
    cancel_booking_from_list,
    show_help,
    show_settings,
    show_language_selection,
    set_language
)
from src.handlers.admin import (
    show_admin_menu,
    show_create_schedule_options,
    create_schedule,
    show_manage_workouts,
    list_workouts,
    show_workouts_by_date,
    show_manage_users,
    list_users,
    show_user_info,
    set_user_role,
    show_workout_info_admin,
    show_workout_participants,
    confirm_delete_workout,
    delete_workout_confirmed
)
from src.utils.decorators import ensure_user_exists


# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, Config.LOG_LEVEL)
)
logger = logging.getLogger(__name__)


class TelegramBot:
    """Класс Telegram бота CrossFit Hub"""
    
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
        
        # Обработчики callback запросов с декоратором ensure_user_exists
        
        # Главное меню
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_main_menu),
                pattern='^main_menu$'
            )
        )
        
        # Расписание
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_schedule_menu),
                pattern='^schedule$'
            )
        )
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_schedule_for_day),
                pattern='^schedule:(today|tomorrow)$'
            )
        )
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_schedule_for_day),
                pattern='^schedule:back$'
            )
        )
        
        # Информация о тренировке
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_workout_info),
                pattern='^workout_info:'
            )
        )
        
        # Запись на тренировку
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(book_workout),
                pattern='^book:'
            )
        )
        
        # Отмена записи (из просмотра тренировки)
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(cancel_booking_from_workout),
                pattern='^cancel_booking:'
            )
        )
        
        # Мои записи
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_my_bookings),
                pattern='^my_bookings$'
            )
        )
        
        # Информация о записи
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_booking_info),
                pattern='^booking_info:'
            )
        )
        
        # Отмена записи (из списка записей)
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(cancel_booking_from_list),
                pattern='^cancel_booking_from_list:'
            )
        )
        
        # Справка
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_help),
                pattern='^help$'
            )
        )
        
        # Настройки
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_settings),
                pattern='^settings$'
            )
        )
        
        # Выбор языка
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_language_selection),
                pattern='^change_language$'
            )
        )
        
        # Установка языка
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(set_language),
                pattern='^set_lang:'
            )
        )
        
        # === АДМИН-ПАНЕЛЬ ===
        
        # Главное меню админа
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_admin_menu),
                pattern='^admin_menu$'
            )
        )
        
        # Создание расписания
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_create_schedule_options),
                pattern='^admin_create_schedule$'
            )
        )
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(create_schedule),
                pattern='^create_schedule:'
            )
        )
        
        # Управление тренировками
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_manage_workouts),
                pattern='^admin_manage_workouts$'
            )
        )
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(list_workouts),
                pattern='^admin_list_workouts$'
            )
        )
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_workouts_by_date),
                pattern='^admin_workouts_date:'
            )
        )
        
        # Управление пользователями
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_manage_users),
                pattern='^admin_manage_users$'
            )
        )
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(list_users),
                pattern='^admin_list_users$'
            )
        )
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_user_info),
                pattern='^admin_user_info:'
            )
        )
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(set_user_role),
                pattern='^admin_set_role:'
            )
        )
        
        # Информация о тренировке (для админа)
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_workout_info_admin),
                pattern='^admin_workout_info:'
            )
        )
        
        # Список участников тренировки
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_workout_participants),
                pattern='^admin_workout_participants:'
            )
        )
        
        # Подтверждение удаления тренировки
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(confirm_delete_workout),
                pattern='^admin_confirm_delete:'
            )
        )
        
        # Удаление тренировки
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(delete_workout_confirmed),
                pattern='^admin_delete_confirmed:'
            )
        )
        
        # Обработчик ошибок
        self.application.add_error_handler(error_handler)
        
        logger.info("Обработчики команд зарегистрированы")
    
    def _wrap_with_user_check(self, handler):
        """Обёртка для применения декоратора ensure_user_exists к callback handlers"""
        return ensure_user_exists(handler)
    
    async def post_init(self, application: Application) -> None:
        """Выполняется после инициализации приложения"""
        logger.info("Инициализация базы данных...")
        await init_db()
        logger.info("База данных инициализирована")
    
    def run(self):
        """Запуск бота"""
        logger.info("Запуск бота CrossFit Hub...")
        
        # Добавляем post_init callback
        self.application.post_init = self.post_init
        
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        logger.info("Бот остановлен")


if __name__ == '__main__':
    bot = TelegramBot()
    bot.run()

