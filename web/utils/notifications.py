"""
Отправка Telegram-уведомлений из веб-приложения
"""
import logging
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


async def notify_athletes_workout_cancelled(token: str, athlete_telegram_ids: list[int],
                                            workout_name: str, workout_datetime: str) -> None:
    """
    Уведомить атлетов об отмене/удалении тренировки.
    Использует Bot напрямую (без Application) — для вызова из FastAPI.
    """
    if not athlete_telegram_ids:
        return

    text = (
        f"❌ *Тренировка отменена*\n\n"
        f"Тренировка *{workout_name}* {workout_datetime} была удалена.\n"
        f"Ваша запись автоматически отменена."
    )

    bot = Bot(token=token)
    async with bot:
        for telegram_id in athlete_telegram_ids:
            try:
                await bot.send_message(chat_id=telegram_id, text=text, parse_mode='Markdown')
            except TelegramError as e:
                logger.warning(f"Не удалось отправить уведомление атлету {telegram_id}: {e}")
