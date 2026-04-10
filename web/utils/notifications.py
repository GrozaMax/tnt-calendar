"""
Отправка Telegram-уведомлений из веб-приложения
"""
from __future__ import annotations

import logging
from telegram import Bot
from telegram.error import TelegramError

from src.locales import get_text

logger = logging.getLogger(__name__)


async def notify_athletes_workout_cancelled(token: str,
                                            athletes: list[dict],
                                            workout_name: str,
                                            workout_datetime: str,
                                            reason: str = "") -> None:
    """
    Уведомить атлетов об отмене/удалении тренировки.
    athletes: список dict с ключами 'telegram_id', 'language', 'notifications_enabled'.
    Использует Bot напрямую (без Application) — для вызова из FastAPI.
    """
    if not athletes:
        return

    bot = Bot(token=token)
    async with bot:
        for athlete in athletes:
            if not athlete.get('notifications_enabled', True):
                continue
            telegram_id = athlete['telegram_id']
            lang = athlete.get('language', 'ru')
            title = get_text('notifications.workout_cancelled_title', lang)
            body = get_text('notifications.workout_cancelled_body', lang,
                            name=workout_name, datetime=workout_datetime)
            text = f"*{title}*\n\n{body}"
            if reason:
                text += "\n\n" + get_text('notifications.cancellation_reason', lang, reason=reason)
            try:
                await bot.send_message(chat_id=telegram_id, text=text, parse_mode='Markdown')
            except TelegramError as e:
                logger.warning(f"Не удалось отправить уведомление атлету {telegram_id}: {e}")
