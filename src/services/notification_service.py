"""
Сервис отправки уведомлений через Telegram
"""
import logging
from typing import Optional
from telegram import Bot, Message
from telegram.error import TelegramError

from src.locales import get_text

logger = logging.getLogger(__name__)


async def notify_trainer_new_booking(bot: Bot, trainer_telegram_id: int,
                                     athlete_name: str, workout_name: str,
                                     workout_datetime: str,
                                     trainer_lang: str = 'ru',
                                     notifications_enabled: bool = True,
                                     guests: int = 0) -> Optional[Message]:
    """Уведомить тренера о новой записи атлета. Возвращает отправленное сообщение или None."""
    if not notifications_enabled:
        return None
        
    athlete_display = athlete_name
    if guests > 0:
        athlete_display += f" (+{guests})"
        
    text = (
        f"*{get_text('notifications.new_booking_title', trainer_lang)}*\n\n"
        + get_text('notifications.new_booking_body', trainer_lang,
                   athlete=athlete_display, workout=workout_name, datetime=workout_datetime)
    )
    try:
        return await bot.send_message(chat_id=trainer_telegram_id, text=text, parse_mode='Markdown')
    except TelegramError as e:
        logger.warning(f"Не удалось отправить уведомление тренеру {trainer_telegram_id}: {e}")
        return None


async def notify_trainer_booking_cancelled(bot: Bot, trainer_telegram_id: int,
                                           athlete_name: str, workout_name: str,
                                           workout_datetime: str,
                                           trainer_lang: str = 'ru',
                                           notifications_enabled: bool = True) -> Optional[Message]:
    """Уведомить тренера об отмене записи атлетом. Возвращает отправленное сообщение или None."""
    if not notifications_enabled:
        return None
    text = (
        f"*{get_text('notifications.booking_cancelled_title', trainer_lang)}*\n\n"
        + get_text('notifications.booking_cancelled_body', trainer_lang,
                   athlete=athlete_name, workout=workout_name, datetime=workout_datetime)
    )
    try:
        return await bot.send_message(chat_id=trainer_telegram_id, text=text, parse_mode='Markdown')
    except TelegramError as e:
        logger.warning(f"Не удалось отправить уведомление тренеру {trainer_telegram_id}: {e}")
        return None


async def notify_athlete_removed_by_trainer(bot: Bot, athlete_telegram_id: int,
                                            workout_name: str, workout_datetime: str,
                                            athlete_lang: str = 'ru',
                                            notifications_enabled: bool = True) -> None:
    """Уведомить атлета об удалении с тренировки тренером"""
    if not notifications_enabled:
        return
    title = get_text('notifications.removed_by_trainer_title', athlete_lang)
    body = get_text('notifications.removed_by_trainer_body', athlete_lang,
                    name=workout_name, datetime=workout_datetime)
    try:
        await bot.send_message(chat_id=athlete_telegram_id, text=f"*{title}*\n\n{body}", parse_mode='Markdown')
    except TelegramError as e:
        logger.warning(f"Не удалось отправить уведомление атлету {athlete_telegram_id}: {e}")


async def notify_athlete_workout_cancelled(bot: Bot, athlete_telegram_id: int,
                                           workout_name: str, workout_datetime: str,
                                           reason: str = "",
                                           athlete_lang: str = 'ru',
                                           notifications_enabled: bool = True) -> None:
    """Уведомить атлета об отмене/удалении тренировки"""
    if not notifications_enabled:
        return
    title = get_text('notifications.workout_cancelled_title', athlete_lang)
    body = get_text('notifications.workout_cancelled_body', athlete_lang,
                    name=workout_name, datetime=workout_datetime)
    text = f"*{title}*\n\n{body}"
    if reason:
        text += "\n\n" + get_text('notifications.cancellation_reason', athlete_lang, reason=reason)
    try:
        await bot.send_message(chat_id=athlete_telegram_id, text=text, parse_mode='Markdown')
    except TelegramError as e:
        logger.warning(f"Не удалось отправить уведомление атлету {athlete_telegram_id}: {e}")
