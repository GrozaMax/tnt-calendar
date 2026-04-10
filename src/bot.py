"""
Главный модуль бота
"""
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from src.config import Config
from src.database import init_db
from src.handlers.base import (
    start_command,
    help_command,
    error_handler,
    handle_text_message,
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
    set_language,
    show_schedule_image,
    toggle_notifications,
)
from src.handlers.admin import (
    show_admin_menu,
    show_admin_workouts,
    show_admin_day_workouts,
    show_workout_details,
    show_users_stats,
    admin_delete_workout_confirm,
    admin_cancel_delete,
    admin_select_trainer,
    admin_assign_trainer,
    show_admin_schedule_image,
    admin_upload_schedule_image_prompt,
    admin_delete_schedule_image,
    handle_admin_photo_upload,
)
from src.handlers.trainer import (
    show_trainer_menu,
    show_trainer_workouts,
    show_trainer_workout_info,
    remove_athlete_from_workout,
    show_free_slots,
    assign_trainer_to_workout
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
                pattern='^schedule:(today|tomorrow|back|\d{4}-\d{2}-\d{2})$'
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

        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(toggle_notifications),
                pattern='^toggle_notifications$'
            )
        )
        
        # === АДМИН-ПАНЕЛЬ (просмотр) ===
        
        # Главное меню админа
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_admin_menu),
                pattern='^admin_menu$'
            )
        )
        
        # Просмотр тренировок
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_admin_workouts),
                pattern='^admin_view_workouts:'
            )
        )
        
        # Детали тренировки
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_workout_details),
                pattern='^admin_workout_details:'
            )
        )
        
        # Статистика пользователей
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_users_stats),
                pattern='^admin_users_stats$'
            )
        )

        # Подтверждение удаления тренировки
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(admin_delete_workout_confirm),
                pattern='^admin_delete_workout_confirm:'
            )
        )

        # Отмена удаления тренировки
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(admin_cancel_delete),
                pattern='^admin_cancel_delete:'
            )
        )

        # Расписание за конкретный день (из недельного выбора)
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_admin_day_workouts),
                pattern='^admin_day:'
            )
        )

        # Картинка расписания (атлет)
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_schedule_image),
                pattern='^schedule_image$'
            )
        )

        # Управление картинкой расписания (админ)
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_admin_schedule_image),
                pattern='^admin_schedule_image$'
            )
        )
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(admin_upload_schedule_image_prompt),
                pattern='^admin_upload_schedule_image$'
            )
        )
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(admin_delete_schedule_image),
                pattern='^admin_delete_schedule_image$'
            )
        )

        # Текстовые сообщения: нижняя панель навигации + ввод причины удаления тренировки
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                handle_text_message
            )
        )

        # Фото от администратора (загрузка картинки расписания)
        self.application.add_handler(
            MessageHandler(
                filters.PHOTO,
                self._wrap_with_user_check(handle_admin_photo_upload)
            )
        )

        # Выбор тренера для назначения
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(admin_select_trainer),
                pattern='^admin_select_trainer:'
            )
        )

        # Назначение тренера
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(admin_assign_trainer),
                pattern='^admin_assign_trainer:'
            )
        )
        
        # === ПАНЕЛЬ ТРЕНЕРА (просмотр) ===
        
        # Главное меню тренера
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_trainer_menu),
                pattern='^trainer_menu$'
            )
        )
        
        # Просмотр тренировок тренера
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_trainer_workouts),
                pattern='^trainer_workouts:'
            )
        )
        
        # Детали тренировки (для тренера)
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_trainer_workout_info),
                pattern='^trainer_workout_info:'
            )
        )

        # Удаление атлета с тренировки (тренером)
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(remove_athlete_from_workout),
                pattern='^trainer_remove_athlete:'
            )
        )

        # Свободные слоты (без тренера)
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(show_free_slots),
                pattern='^trainer_free_slots$'
            )
        )

        # Назначение тренера на слот
        self.application.add_handler(
            CallbackQueryHandler(
                self._wrap_with_user_check(assign_trainer_to_workout),
                pattern='^trainer_assign:'
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

