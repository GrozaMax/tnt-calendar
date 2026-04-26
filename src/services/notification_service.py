"""
Сервис отправки уведомлений через Telegram
"""
import logging
from typing import Optional
from datetime import datetime
from telegram import Bot, Message
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from src.locales import get_text
from src.database.connection import async_session_maker
from src.models import Workout, Booking, BookingStatus, User

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


async def notify_athlete_workout_reminder(bot: Bot, athlete_telegram_id: int,
                                          workout_name: str, workout_datetime: str,
                                          athlete_lang: str = 'ru') -> None:
    """Уведомить атлета о предстоящей тренировке"""
    title = get_text('notifications.workout_reminder_title', athlete_lang)
    body = get_text('notifications.workout_reminder_body', athlete_lang,
                    name=workout_name, datetime=workout_datetime)
    try:
        await bot.send_message(chat_id=athlete_telegram_id, text=f"*{title}*\n\n{body}", parse_mode='Markdown')
    except TelegramError as e:
        logger.warning(f"Не удалось отправить напоминание атлету {athlete_telegram_id}: {e}")


async def check_workout_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Фоновая задача проверки тренировок и отправки напоминаний"""
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload

    now = datetime.now()
    logger.info(f"[reminders] Проверка напоминаний, now={now.strftime('%Y-%m-%d %H:%M:%S')}")

    async with async_session_maker() as session:
        # Находим все активные записи (где reminder_sent=False),
        # подгружаем тренировку и юзера
        query = (
            select(Booking)
            .options(
                joinedload(Booking.workout),
                joinedload(Booking.user)
            )
            .where(
                Booking.status == BookingStatus.ACTIVE,
                Booking.reminder_sent == False
            )
        )
        result = await session.execute(query)
        bookings = result.scalars().all()

        logger.info(f"[reminders] Найдено букингов с reminder_sent=False: {len(bookings)}")

        sent_count = 0
        for booking in bookings:
            user = booking.user
            workout = booking.workout

            # Проверяем, нужны ли вообще уведомления
            if not user.notifications_enabled:
                logger.info(f"[reminders] Пропуск booking#{booking.id}: уведомления выключены у {user.full_name}")
                continue

            # Считаем сколько минут осталось до тренировки
            diff = workout.datetime - now
            minutes_left = diff.total_seconds() / 60.0

            logger.info(
                f"[reminders] booking#{booking.id}: "
                f"workout={workout.name} at {workout.datetime.strftime('%Y-%m-%d %H:%M')}, "
                f"user={user.full_name}, "
                f"minutes_left={minutes_left:.1f}, "
                f"reminder_minutes={user.reminder_minutes}"
            )

            # Тренировка уже прошла — молча помечаем как отправленное
            if minutes_left <= 0:
                booking.reminder_sent = True
                sent_count += 1
                logger.info(f"[reminders] ⏭ Тренировка уже прошла, помечаю как отправленное: booking#{booking.id} ({workout.name})")
                continue

            # Если время до тренировки меньше или равно настройке напоминания — отправляем
            if minutes_left <= user.reminder_minutes:
                time_str = workout.datetime.strftime('%H:%M')
                await notify_athlete_workout_reminder(
                    bot=context.bot,
                    athlete_telegram_id=user.telegram_id,
                    workout_name=workout.name,
                    workout_datetime=time_str,
                    athlete_lang=user.language
                )
                
                # Отмечаем как отправленное
                booking.reminder_sent = True
                sent_count += 1
                logger.info(f"[reminders] ✅ Напоминание отправлено: {user.full_name} → {workout.name} в {time_str}")
        
        if sent_count > 0:
            await session.commit()
            logger.info(f"[reminders] Обработано: {sent_count}")

