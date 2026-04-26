"""
Обработчики для тренеров

Функционал просмотра для тренеров:
- Просмотр своего расписания
- Просмотр количества записавшихся
- Просмотр списка участников
"""
from datetime import date, timedelta
from telegram import Update
from telegram.ext import ContextTypes

from src.database import get_session
from src.database.repositories import WorkoutRepository, BookingRepository
from src.keyboards.athlete_keyboards import format_dt
from src.keyboards.trainer_keyboards import (
    trainer_section_keyboard,
    trainer_workouts_list_keyboard,
    trainer_workout_details_keyboard,
    trainer_free_slots_keyboard,
    trainer_assigned_keyboard
)
from src.locales import get_text
from src.models import User, UserRole, BookingStatus
from src.services.booking_service import BookingService
from src.services.notification_service import notify_athlete_removed_by_trainer
from src.utils.decorators import role_required


@role_required(UserRole.TRAINER, UserRole.ADMIN)
async def show_trainer_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню тренера (раздел 'Тренерская')"""
    query = update.callback_query
    await query.answer()
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    title = get_text('trainer.section_title', lang)
    await query.edit_message_text(
        f"*{title}*\n\n{get_text('trainer.select_section', lang)}",
        reply_markup=trainer_section_keyboard(lang),
        parse_mode='Markdown'
    )


@role_required(UserRole.TRAINER, UserRole.ADMIN)
async def show_trainer_workouts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать тренировки тренера"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    # Получаем период из callback_data
    _, period = query.data.split(':')
    
    if period == 'today':
        target_date = date.today()
        date_end = target_date
        title = get_text('trainer.today_workouts', lang)
    elif period == 'tomorrow':
        target_date = date.today() + timedelta(days=1)
        date_end = target_date
        title = get_text('trainer.tomorrow_workouts', lang)
    else:  # week
        target_date = date.today()
        date_end = target_date + timedelta(days=7)
        title = get_text('trainer.week_workouts', lang)
    
    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        workouts = await workout_repo.get_by_date_range(
            target_date,
            date_end
        )
        
        # Фильтруем только тренировки этого тренера
        workouts = [w for w in workouts if w.trainer_id == user.id]
    
    if not workouts:
        text = f"📅 *{title}*\n\n"
        text += f"{get_text('trainer.no_workouts', lang)}\n\n"
        text += f"{get_text('trainer.use_web', lang)}\n"
        text += "https://tnt-calendar-adminweb.duckdns.org"
        
        keyboard = trainer_workouts_list_keyboard([], lang)

        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        return

    text = f"*{title}*\n\n{get_text('trainer.found_count', lang, count=len(workouts))}\n\n"

    keyboard = trainer_workouts_list_keyboard(workouts, lang)
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


async def _render_trainer_workout(query, user: User, workout_id: int, lang: str):
    """Общая логика отображения тренировки для тренера/админа."""

    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        booking_repo = BookingRepository(session)

        workout = await workout_repo.get_by_id(workout_id, load_relations=True)

        if not workout:
            await query.answer(get_text('trainer.workout_not_found', lang), show_alert=True)
            return

        if workout.trainer_id != user.id and user.role != UserRole.ADMIN:
            await query.answer(get_text('trainer.not_your_workout', lang), show_alert=True)
            return

        from html import escape
        text = f"📋 <b>{escape(workout.name)}</b>\n\n"
        text += f"🕐 {format_dt(workout.datetime, '%d.%m.%Y %H:%M', lang)}\n"
        text += f"{get_text('schedule.duration', lang, duration=workout.duration)}\n"
        text += f"{get_text('schedule.participants', lang, count=workout.current_participants, max=workout.max_participants)}\n"

        if workout.description:
            text += f"\n📝 {escape(workout.description)}\n"

        bookings = await booking_repo.get_workout_bookings(
            workout_id, status=BookingStatus.ACTIVE, load_relations=True
        )

        if bookings:
            text += f"\n{get_text('admin.participants_list', lang)}\n\n"
            for i, booking in enumerate(bookings[:20], 1):
                text += f"{i}. {escape(booking.user.full_name)}"
                if booking.user.username:
                    text += f" (@{escape(booking.user.username)})"
                if booking.guests > 0:
                    text += f" (+{booking.guests})"
                text += "\n"
            if len(bookings) > 20:
                text += f"\n{get_text('admin.and_more', lang, count=len(bookings) - 20)}"
        else:
            text += f"\n{get_text('admin.no_participants', lang)}"

        keyboard = trainer_workout_details_keyboard(lang)

        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')


@role_required(UserRole.TRAINER, UserRole.ADMIN)
async def remove_athlete_from_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить атлета с тренировки"""
    query = update.callback_query

    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'

    parts = query.data.split(':')
    booking_id = int(parts[1])
    workout_id = int(parts[2])

    athlete_telegram_id = None
    athlete_lang = 'ru'
    athlete_notifications_enabled = True
    workout_name = ''
    workout_datetime_str = ''

    async with get_session() as session:
        booking_repo = BookingRepository(session)
        booking_service = BookingService(session)

        booking = await booking_repo.get_by_id(booking_id, load_relations=True)
        if booking and booking.user:
            athlete_telegram_id = booking.user.telegram_id
            athlete_lang = booking.user.language or 'ru'
            athlete_notifications_enabled = booking.user.notifications_enabled
        if booking and booking.workout:
            workout_name = booking.workout.name
            workout_datetime_str = format_dt(booking.workout.datetime, '%d.%m.%Y %H:%M', lang)

        is_admin = user.is_admin()
        success, message = await booking_service.cancel_booking_by_trainer(
            booking_id=booking_id,
            trainer_id=user.id,
            is_admin=is_admin,
            lang=lang
        )

    await query.answer(message, show_alert=True)

    if success and athlete_telegram_id:
        await notify_athlete_removed_by_trainer(
            bot=context.bot,
            athlete_telegram_id=athlete_telegram_id,
            workout_name=workout_name,
            workout_datetime=workout_datetime_str,
            athlete_lang=athlete_lang,
            notifications_enabled=athlete_notifications_enabled,
        )

    if success:
        await _render_trainer_workout(query, user, workout_id, lang)


@role_required(UserRole.TRAINER, UserRole.ADMIN)
async def show_trainer_workout_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о тренировке (для тренера)"""
    query = update.callback_query
    await query.answer()

    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'

    _, workout_id_str = query.data.split(':')
    await _render_trainer_workout(query, user, int(workout_id_str), lang)


async def _render_free_slots(query, lang: str):
    """Отрисовать список свободных слотов в сообщение."""

    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        workouts = await workout_repo.get_unassigned_workouts(days=7)

    if not workouts:
        text = f"*{get_text('trainer.free_slots_btn', lang)}*\n\n{get_text('trainer.no_free_slots', lang)}"
        keyboard = trainer_free_slots_keyboard([], lang)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        return

    text = f"*{get_text('trainer.free_slots_btn', lang)}*\n\n{get_text('trainer.select_to_assign', lang)}\n"
    keyboard = trainer_free_slots_keyboard(workouts, lang)
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')


@role_required(UserRole.TRAINER, UserRole.ADMIN)
async def show_free_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать тренировки без назначенного тренера"""
    query = update.callback_query
    await query.answer()

    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'

    await _render_free_slots(query, lang)


@role_required(UserRole.TRAINER, UserRole.ADMIN)
async def assign_trainer_to_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тренер назначает себя на тренировку"""
    query = update.callback_query
    await query.answer()

    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'

    _, workout_id = query.data.split(':')
    workout_id = int(workout_id)

    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        workout = await workout_repo.get_by_id(workout_id)

        if not workout:
            await query.answer(get_text('trainer.workout_not_found', lang), show_alert=True)
            return

        if workout.trainer_id is not None:
            await query.answer(get_text('trainer.already_assigned', lang), show_alert=True)
            return

        await workout_repo.assign_trainer(workout_id, user.id)
        await session.commit()

    await query.answer()

    date_str = format_dt(workout.datetime, '%d.%m %H:%M', lang)
    text = (
        f"✅ *Вы назначены на тренировку!*\n\n"
        f"🏋️ {workout.name}\n"
        f"📅 {date_str}\n"
        f"👥 {workout.current_participants}/{workout.max_participants} участников"
    )
    keyboard = trainer_assigned_keyboard(lang)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
