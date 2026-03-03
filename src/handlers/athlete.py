"""
Обработчики для атлетов
"""
from datetime import date, datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes

from src.database import get_session
from src.database.repositories import WorkoutRepository, BookingRepository, UserRepository
from src.services.booking_service import BookingService
from src.services.notification_service import notify_trainer_new_booking, notify_trainer_booking_cancelled
from src.keyboards.athlete_keyboards import (
    main_menu_keyboard,
    schedule_days_keyboard,
    workouts_list_keyboard,
    workout_actions_keyboard,
    my_bookings_keyboard,
    booking_info_keyboard,
    back_to_main_menu_keyboard,
    settings_keyboard,
    language_selection_keyboard
)
from src.locales import get_text
from src.models import User


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать главное меню"""
    query = update.callback_query
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    text = get_text('common.welcome', lang, name=user.first_name if user else "Атлет")
    is_admin = user and user.is_admin()
    is_trainer = user and user.is_trainer() and not user.is_admin()
    keyboard = main_menu_keyboard(lang, is_admin=is_admin, is_trainer=is_trainer)
    
    if query:
        await query.answer()
        await query.edit_message_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)


async def show_schedule_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню выбора дня"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    text = get_text('schedule.select_day', lang)
    keyboard = schedule_days_keyboard(lang)
    
    await query.edit_message_text(text, reply_markup=keyboard)


async def show_schedule_for_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать расписание на выбранный день"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    # Определяем день (today или tomorrow)
    _, day = query.data.split(':')
    
    if day == 'today':
        target_date = date.today()
        day_name = get_text('schedule.today', lang)
    else:  # tomorrow
        target_date = date.today() + timedelta(days=1)
        day_name = get_text('schedule.tomorrow', lang)
    
    # Сохраняем текущую дату в контекст
    context.user_data['current_schedule_date'] = target_date
    context.user_data['current_schedule_day'] = day
    
    # Получаем тренировки
    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        all_workouts = await workout_repo.get_by_date(target_date, load_relations=True)
    
    # Фильтруем прошедшие тренировки (только для сегодняшнего дня)
    if day == 'today':
        now = datetime.now()
        workouts = [w for w in all_workouts if w.datetime > now]
    else:
        workouts = all_workouts
    
    if not workouts:
        text = f"📅 *{day_name}* ({target_date.strftime('%d.%m.%Y')})\n\n"
        text += get_text('schedule.no_workouts', lang)
        keyboard = schedule_days_keyboard(lang)
    else:
        text = f"📅 *{day_name}* ({target_date.strftime('%d.%m.%Y')})\n\n"
        text += "Выберите тренировку:"
        keyboard = workouts_list_keyboard(workouts, lang)
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


async def show_workout_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о конкретной тренировке"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    # Получаем ID тренировки из callback_data
    _, workout_id = query.data.split(':')
    workout_id = int(workout_id)
    
    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        booking_repo = BookingRepository(session)
        
        workout = await workout_repo.get_by_id(workout_id, load_relations=True)
        
        if not workout:
            await query.edit_message_text("❌ Тренировка не найдена")
            return
        
        # Проверяем, записан ли пользователь
        is_booked = False
        if user:
            booking = await booking_repo.get_by_user_and_workout(user.id, workout_id)
            is_booked = booking and booking.is_active
        
        # Формируем текст
        text = f"📋 *{workout.name}*\n\n"
        text += f"🕐 {workout.datetime.strftime('%d.%m.%Y %H:%M')}\n"
        text += f"⏱ {workout.duration} мин\n"
        text += f"👤 Тренер: {workout.trainer.full_name}\n"
        text += f"👥 Записалось: {workout.current_participants}/{workout.max_participants}\n"
        
        if workout.description:
            text += f"\n📝 {workout.description}\n"
        
        if is_booked:
            text += "\n✅ *Вы записаны на эту тренировку*"
        elif workout.is_full:
            text += "\n❌ *Свободных мест нет*"
        
        keyboard = workout_actions_keyboard(
            workout_id,
            is_booked=is_booked,
            is_full=workout.is_full,
            lang=lang
        )
        
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )


async def book_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Записаться на тренировку"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    # Получаем ID тренировки
    _, workout_id = query.data.split(':')
    workout_id = int(workout_id)
    
    async with get_session() as session:
        booking_service = BookingService(session)
        workout_repo = WorkoutRepository(session)
        
        # Создаём запись
        success, message, booking = await booking_service.create_booking(
            user_id=user.id,
            workout_id=workout_id
        )
        
        if success:
            # Получаем информацию о тренировке для подтверждения
            workout = await workout_repo.get_by_id(workout_id, load_relations=True)

            confirmation_text = get_text(
                'booking.success',
                lang,
                name=workout.name,
                datetime=workout.datetime.strftime('%d.%m.%Y %H:%M'),
                trainer=workout.trainer.full_name if workout.trainer else 'Не назначен'
            )

            await query.answer(get_text('booking.success', lang)[:200], show_alert=True)
            await query.edit_message_text(
                confirmation_text,
                reply_markup=back_to_main_menu_keyboard(lang)
            )

            # Уведомляем тренера о новой записи
            if workout.trainer and workout.trainer.telegram_id:
                athlete_name = user.full_name
                await notify_trainer_new_booking(
                    bot=context.bot,
                    trainer_telegram_id=workout.trainer.telegram_id,
                    athlete_name=athlete_name,
                    workout_name=workout.name,
                    workout_datetime=workout.datetime.strftime('%d.%m.%Y %H:%M')
                )
        else:
            # Получаем информацию о тренировке для отображения
            workout = await workout_repo.get_by_id(workout_id, load_relations=True)
            
            # Формируем текст с ошибкой
            error_text = f"⚠️ *Не удалось записаться*\n\n"
            error_text += f"{message}\n\n"
            error_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
            
            if workout:
                error_text += f"📋 *{workout.name}*\n"
                error_text += f"🕐 {workout.datetime.strftime('%d.%m.%Y %H:%M')}\n"
                error_text += f"👤 Тренер: {workout.trainer.full_name}\n"
                error_text += f"👥 Записалось: {workout.current_participants}/{workout.max_participants}\n"
            
            await query.edit_message_text(
                error_text,
                reply_markup=back_to_main_menu_keyboard(lang),
                parse_mode='Markdown'
            )


async def cancel_booking_from_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменить запись из просмотра тренировки"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    # Получаем ID тренировки
    _, workout_id = query.data.split(':')
    workout_id = int(workout_id)
    
    async with get_session() as session:
        booking_repo = BookingRepository(session)
        booking_service = BookingService(session)
        workout_repo = WorkoutRepository(session)

        # Находим запись
        booking = await booking_repo.get_by_user_and_workout(user.id, workout_id)

        if not booking:
            await query.answer("❌ Запись не найдена", show_alert=True)
            return

        # Отменяем запись
        success, message = await booking_service.cancel_booking(booking.id, user.id)

        await query.answer(message, show_alert=True)

        if success:
            await query.edit_message_text(
                get_text('booking.cancelled', lang),
                reply_markup=back_to_main_menu_keyboard(lang)
            )

            # Уведомляем тренера об отмене
            workout = await workout_repo.get_by_id(workout_id, load_relations=True)
            if workout and workout.trainer and workout.trainer.telegram_id:
                await notify_trainer_booking_cancelled(
                    bot=context.bot,
                    trainer_telegram_id=workout.trainer.telegram_id,
                    athlete_name=user.full_name,
                    workout_name=workout.name,
                    workout_datetime=workout.datetime.strftime('%d.%m.%Y %H:%M')
                )
        else:
            await show_workout_info(update, context)


async def show_my_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать записи пользователя"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    async with get_session() as session:
        booking_service = BookingService(session)
        bookings = await booking_service.get_user_active_bookings(user.id)
    
    if not bookings:
        text = get_text('my_bookings.no_bookings', lang)
        keyboard = back_to_main_menu_keyboard(lang)
    else:
        text = get_text('my_bookings.title', lang) + "\n\n"
        text += get_text('my_bookings.upcoming', lang)
        keyboard = my_bookings_keyboard(bookings, lang)
    
    await query.edit_message_text(text, reply_markup=keyboard)


async def show_booking_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о конкретной записи"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    # Получаем ID записи
    _, booking_id = query.data.split(':')
    booking_id = int(booking_id)
    
    async with get_session() as session:
        booking_repo = BookingRepository(session)
        booking = await booking_repo.get_by_id(booking_id, load_relations=True)
        
        if not booking or booking.user_id != user.id:
            await query.answer("❌ Запись не найдена", show_alert=True)
            return
        
        workout = booking.workout
        
        text = get_text(
            'my_bookings.booking_info',
            lang,
            name=workout.name,
            datetime=workout.datetime.strftime('%d.%m.%Y %H:%M'),
            trainer=workout.trainer.full_name,
            status="✅ Активна" if booking.is_active else "❌ Отменена"
        )
        
        keyboard = booking_info_keyboard(booking_id, lang)
        await query.edit_message_text(text, reply_markup=keyboard)


async def cancel_booking_from_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменить запись из списка записей"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    # Получаем ID записи
    _, booking_id = query.data.split(':')
    booking_id = int(booking_id)
    
    async with get_session() as session:
        booking_repo = BookingRepository(session)
        booking_service = BookingService(session)

        # Получаем данные записи до отмены (для уведомления)
        booking = await booking_repo.get_by_id(booking_id, load_relations=True)

        success, message = await booking_service.cancel_booking(booking_id, user.id)

        await query.answer(message, show_alert=True)

        if success:
            # Уведомляем тренера об отмене
            if booking and booking.workout and booking.workout.trainer and booking.workout.trainer.telegram_id:
                await notify_trainer_booking_cancelled(
                    bot=context.bot,
                    trainer_telegram_id=booking.workout.trainer.telegram_id,
                    athlete_name=user.full_name,
                    workout_name=booking.workout.name,
                    workout_datetime=booking.workout.datetime.strftime('%d.%m.%Y %H:%M')
                )

            # Возвращаемся к списку записей
            context.user_data['temp_callback_data'] = 'my_bookings'
            await show_my_bookings(update, context)
        else:
            await show_booking_info(update, context)


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать справку"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    text = get_text('common.help', lang)
    keyboard = back_to_main_menu_keyboard(lang)
    
    if query:
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )


async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню настроек"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    text = get_text('menu.settings', lang)
    keyboard = settings_keyboard(lang)
    
    await query.edit_message_text(text, reply_markup=keyboard)


async def show_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать выбор языка"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    current_lang = user.language if user else 'ru'
    
    lang_names = {
        'ru': '🇷🇺 Русский',
        'ua': '🇺🇦 Українська',
        'en': '🇬🇧 English',
        'de': '🇩🇪 Deutsch',
        'ge': '🇬🇪 ქართული'
    }
    
    text = f"🌐 Выберите язык / Choose language\n\n"
    text += f"Текущий язык / Current: {lang_names.get(current_lang, 'Русский')}"
    
    keyboard = language_selection_keyboard()
    
    await query.edit_message_text(text, reply_markup=keyboard)


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранить выбранный язык"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    
    # Получаем код языка из callback_data
    _, lang_code = query.data.split(':')
    
    # Обновляем язык пользователя в БД
    async with get_session() as session:
        user_repo = UserRepository(session)
        await user_repo.update_language(user.id, lang_code)
        await session.commit()
    
    # Обновляем язык в объекте пользователя
    user.language = lang_code
    
    # Сообщения на разных языках
    success_messages = {
        'ru': '✅ Язык изменён на Русский',
        'ua': '✅ Мова змінена на Українську',
        'en': '✅ Language changed to English',
        'de': '✅ Sprache auf Deutsch geändert',
        'ge': '✅ ენა შეიცვალა ქართულად'
    }
    
    await query.answer(success_messages.get(lang_code, '✅ Language changed'), show_alert=True)
    
    # Возвращаемся в главное меню
    await show_main_menu(update, context)

