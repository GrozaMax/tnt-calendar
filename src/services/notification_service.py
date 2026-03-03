"""
Сервис отправки уведомлений через Telegram
"""
import logging
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


async def notify_trainer_new_booking(bot: Bot, trainer_telegram_id: int,
                                     athlete_name: str, workout_name: str,
                                     workout_datetime: str) -> None:
    """Уведомить тренера о новой записи атлета на его тренировку"""
    text = (
        f"👤 *Новая запись на тренировку!*\n\n"
        f"Атлет: *{athlete_name}*\n"
        f"Тренировка: *{workout_name}*\n"
        f"Дата/время: *{workout_datetime}*"
    )
    try:
        await bot.send_message(
            chat_id=trainer_telegram_id,
            text=text,
            parse_mode='Markdown'
        )
    except TelegramError as e:
        logger.warning(f"Не удалось отправить уведомление тренеру {trainer_telegram_id}: {e}")


async def notify_trainer_booking_cancelled(bot: Bot, trainer_telegram_id: int,
                                            athlete_name: str, workout_name: str,
                                            workout_datetime: str) -> None:
    """Уведомить тренера об отмене записи атлетом"""
    text = (
        f"🚫 *Отмена записи на тренировку*\n\n"
        f"Атлет: *{athlete_name}*\n"
        f"Тренировка: *{workout_name}*\n"
        f"Дата/время: *{workout_datetime}*"
    )
    try:
        await bot.send_message(
            chat_id=trainer_telegram_id,
            text=text,
            parse_mode='Markdown'
        )
    except TelegramError as e:
        logger.warning(f"Не удалось отправить уведомление тренеру {trainer_telegram_id}: {e}")


async def notify_athlete_workout_cancelled(bot: Bot, athlete_telegram_id: int,
                                           workout_name: str, workout_datetime: str) -> None:
    """Уведомить атлета об отмене/удалении тренировки"""
    text = (
        f"❌ *Тренировка отменена*\n\n"
        f"Тренировка *{workout_name}* {workout_datetime} была удалена.\n"
        f"Ваша запись автоматически отменена."
    )
    try:
        await bot.send_message(
            chat_id=athlete_telegram_id,
            text=text,
            parse_mode='Markdown'
        )
    except TelegramError as e:
        logger.warning(f"Не удалось отправить уведомление атлету {athlete_telegram_id}: {e}")
