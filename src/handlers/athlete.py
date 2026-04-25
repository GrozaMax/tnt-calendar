"""
Обработчики для атлетов
"""
from datetime import date, datetime, timedelta
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from src.database import get_session
from src.database.repositories import WorkoutRepository, BookingRepository, UserRepository
from src.database.repositories.settings_repository import SettingsRepository
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
    language_selection_keyboard,
    format_dt,
)
from src.locales import get_text
from src.models import User, UserRole


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать главное меню"""
    query = update.callback_query
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'

    async with get_session() as session:
        max_per_day = await SettingsRepository(session).get_max_bookings_per_day()

    text = get_text(
        'common.welcome',
        lang,
        name=user.first_name if user else "Атлет",
        max_per_day=max_per_day,
    )
    is_admin = user and user.is_admin()
    is_trainer = user and user.is_trainer() and not user.is_admin()
    keyboard = main_menu_keyboard(lang, is_admin=is_admin, is_trainer=is_trainer)
    
    if query:
        await query.answer()
        await query.edit_message_text(text, reply_markup=keyboard)
    else:
        msg = await update.message.reply_text(text, reply_markup=keyboard)
        context.user_data['nav_message_id'] = msg.message_id
    context.user_data['current_screen'] = 'menu'


async def show_schedule_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню выбора дня"""
    query = update.callback_query
    await query.answer()

    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    is_trainer_or_admin = user and user.has_trainer_permissions()

    text = get_text('schedule.select_day', lang)
    back = 'trainer_menu' if is_trainer_or_admin else 'main_menu'
    keyboard = schedule_days_keyboard(lang, back_callback=back)

    await query.edit_message_text(text, reply_markup=keyboard)


async def show_schedule_for_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать расписание на выбранный день"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    # Определяем дату: ISO-строка YYYY-MM-DD, 'today', 'tomorrow', или 'back'
    _, day = query.data.split(':', 1)

    if day == 'today':
        target_date = date.today()
    elif day == 'tomorrow':
        target_date = date.today() + timedelta(days=1)
    elif day == 'back':
        target_date = context.user_data.get('current_schedule_date', date.today())
    else:
        target_date = date.fromisoformat(day)

    day_name = format_dt(target_date, '%d.%m.%Y', lang)

    # Сохраняем текущую дату в контекст
    context.user_data['current_schedule_date'] = target_date

    # Получаем тренировки
    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        all_workouts = await workout_repo.get_by_date(target_date, load_relations=True)

    # Фильтруем прошедшие тренировки для сегодняшнего дня
    if target_date == date.today():
        now = datetime.now()
        workouts = [w for w in all_workouts if w.datetime > now]
    else:
        workouts = all_workouts
    
    is_trainer_or_admin = user and user.has_trainer_permissions()
    back = 'trainer_menu' if is_trainer_or_admin else 'main_menu'

    if not workouts:
        text = f"📅 *{day_name}*\n\n"
        text += get_text('schedule.no_workouts', lang)
        keyboard = schedule_days_keyboard(lang, back_callback=back)
    else:
        text = f"📅 *{day_name}*\n\n"
        text += get_text('schedule.select_workout', lang)
        keyboard = workouts_list_keyboard(workouts, lang)
    
    try:
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    except BadRequest:
        pass  # сообщение уже содержит тот же текст


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
            await query.edit_message_text(get_text('schedule.workout_not_found', lang))
            return

        # Проверяем, записан ли пользователь
        is_booked = False
        if user:
            booking = await booking_repo.get_by_user_and_workout(user.id, workout_id)
            is_booked = booking and booking.is_active

        trainer_name = workout.trainer.full_name if workout.trainer else get_text('schedule.no_trainer', lang)

        from html import escape

        # Формируем текст
        text = f"📋 <b>{escape(workout.name)}</b>\n\n"
        text += get_text('schedule.time', lang, time=format_dt(workout.datetime, '%d.%m.%Y %H:%M', lang)) + "\n"
        text += get_text('schedule.duration', lang, duration=workout.duration) + "\n"
        text += get_text('schedule.trainer', lang, name=escape(trainer_name)) + "\n"
        text += get_text('schedule.participants', lang, count=workout.current_participants, max=workout.max_participants) + "\n"

        if workout.description:
            text += f"\n📝 {escape(workout.description)}\n"

        # Добавляем список записавшихся
        if workout.bookings:
            text += "\n" + get_text('admin.participants_list', lang) + "\n"
            for b in workout.bookings:
                if b.is_active:
                    user_str = escape(b.user.full_name) if b.user else "Unknown"
                    if b.guests > 0:
                        user_str += f" (+{b.guests})"
                    text += f"• {user_str}\n"

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        is_trainer_or_admin = user and user.has_trainer_permissions()

        if is_trainer_or_admin:
            # Тренер/Админ: только просмотр, без кнопок записи
            keyboard_rows = [
                [InlineKeyboardButton(get_text('menu.back', lang), callback_data='schedule:back')]
            ]
            keyboard = InlineKeyboardMarkup(keyboard_rows)
        else:
            if is_booked:
                text += "\n<b>" + get_text('schedule.workout_booked', lang) + "</b>"
            elif workout.is_full:
                text += "\n<b>" + get_text('schedule.full', lang) + "</b>"
            keyboard = workout_actions_keyboard(
                workout_id,
                is_booked=is_booked,
                is_full=workout.is_full,
                lang=lang
            )

        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )


async def book_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Записаться на тренировку"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    # Получаем ID тренировки и проверяем тип записи
    action, workout_id_str = query.data.split(':')
    workout_id = int(workout_id_str)
    guests = 1 if action == 'book_plus_one' else 0
    
    async with get_session() as session:
        booking_service = BookingService(session)
        workout_repo = WorkoutRepository(session)
        
        # Создаём запись
        success, message, _ = await booking_service.create_booking(
            user_id=user.id,
            workout_id=workout_id,
            lang=lang,
            guests=guests
        )
        
        if success:
            # Получаем информацию о тренировке для подтверждения
            workout = await workout_repo.get_by_id(workout_id, load_relations=True)

            confirmation_text = get_text(
                'booking.success',
                lang,
                name=workout.name,
                datetime=format_dt(workout.datetime, '%d.%m.%Y %H:%M', lang),
                trainer=workout.trainer.full_name if workout.trainer else 'Не назначен'
            )

            await query.answer(get_text('booking.success', lang)[:200], show_alert=True)
            await query.edit_message_text(
                confirmation_text,
                reply_markup=back_to_main_menu_keyboard(lang)
            )
            context.user_data['current_screen'] = None

            # Уведомляем тренера о новой записи
            if workout.trainer and workout.trainer.telegram_id:
                sent = await notify_trainer_new_booking(
                    bot=context.bot,
                    trainer_telegram_id=workout.trainer.telegram_id,
                    athlete_name=user.full_name,
                    workout_name=workout.name,
                    workout_datetime=format_dt(workout.datetime, '%d.%m.%Y %H:%M', lang),
                    trainer_lang=workout.trainer.language or 'ru',
                    notifications_enabled=workout.trainer.notifications_enabled,
                    guests=guests
                )
                # После уведомления сбрасываем nav у тренера — чтобы следующий запрос создал новое сообщение внизу
                if sent:
                    trainer_ud = context.application.user_data.get(workout.trainer.telegram_id)
                    if isinstance(trainer_ud, dict):
                        trainer_ud.pop('nav_message_id', None)
                        trainer_ud['current_screen'] = None
        else:
            # Получаем информацию о тренировке для отображения
            workout = await workout_repo.get_by_id(workout_id, load_relations=True)
            
            # Формируем текст с ошибкой
            error_text = f"{get_text('common.error', lang)}\n\n"
            error_text += f"{message}\n\n"
            error_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
            
            if workout:
                trainer_name = workout.trainer.full_name if workout.trainer else get_text('schedule.no_trainer', lang)
                error_text += f"📋 *{workout.name}*\n"
                error_text += get_text('schedule.time', lang, time=format_dt(workout.datetime, '%d.%m.%Y %H:%M', lang)) + "\n"
                error_text += get_text('schedule.trainer', lang, name=trainer_name) + "\n"
                error_text += get_text('schedule.participants', lang, count=workout.current_participants, max=workout.max_participants) + "\n"
            
            await query.edit_message_text(
                error_text,
                reply_markup=back_to_main_menu_keyboard(lang),
                parse_mode='Markdown'
            )
            context.user_data['current_screen'] = None


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
            await query.answer(get_text('booking.not_found', lang), show_alert=True)
            return

        # Отменяем запись
        success, message = await booking_service.cancel_booking(booking.id, user.id, lang=lang)

        await query.answer(message, show_alert=True)

        if success:
            await query.edit_message_text(
                get_text('booking.cancelled', lang),
                reply_markup=back_to_main_menu_keyboard(lang)
            )

            # Уведомляем тренера об отмене
            workout = await workout_repo.get_by_id(workout_id, load_relations=True)
            if workout and workout.trainer and workout.trainer.telegram_id:
                sent = await notify_trainer_booking_cancelled(
                    bot=context.bot,
                    trainer_telegram_id=workout.trainer.telegram_id,
                    athlete_name=user.full_name,
                    workout_name=workout.name,
                    workout_datetime=format_dt(workout.datetime, '%d.%m.%Y %H:%M', lang),
                    trainer_lang=workout.trainer.language or 'ru',
                    notifications_enabled=workout.trainer.notifications_enabled,
                )
                if sent:
                    trainer_ud = context.application.user_data.get(workout.trainer.telegram_id)
                    if isinstance(trainer_ud, dict):
                        trainer_ud.pop('nav_message_id', None)
                        trainer_ud['current_screen'] = None
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
            await query.answer(get_text('booking.not_found', lang), show_alert=True)
            return

        workout = booking.workout
        trainer_name = workout.trainer.full_name if workout.trainer else get_text('schedule.no_trainer', lang)

        from html import escape

        text = get_text(
            'my_bookings.booking_info',
            lang,
            name=escape(workout.name),
            datetime=format_dt(workout.datetime, '%d.%m.%Y %H:%M', lang),
            trainer=escape(trainer_name),
            status=get_text('booking.status_active', lang) if booking.is_active else get_text('booking.status_cancelled', lang)
        )
        if booking.guests > 0:
            text += f"\n👥 Гостей: {booking.guests}"

        # Явно загружаем список участников тренировки
        from src.models import BookingStatus
        workout_bookings = await booking_repo.get_workout_bookings(
            workout.id, 
            status=BookingStatus.ACTIVE, 
            load_relations=True
        )

        if workout_bookings:
            text += "\n\n" + get_text('admin.participants_list', lang) + "\n"
            for b in workout_bookings:
                user_str = escape(b.user.full_name) if b.user else "Unknown"
                if b.guests > 0:
                    user_str += f" (+{b.guests})"
                text += f"• {user_str}\n"
        
        keyboard = booking_info_keyboard(booking_id, lang)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')


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

        success, message = await booking_service.cancel_booking(booking_id, user.id, lang=lang)

        await query.answer(message, show_alert=True)

        if success:
            # Уведомляем тренера об отмене
            if booking and booking.workout and booking.workout.trainer and booking.workout.trainer.telegram_id:
                tr = booking.workout.trainer
                sent = await notify_trainer_booking_cancelled(
                    bot=context.bot,
                    trainer_telegram_id=tr.telegram_id,
                    athlete_name=user.full_name,
                    workout_name=booking.workout.name,
                    workout_datetime=format_dt(booking.workout.datetime, '%d.%m.%Y %H:%M', lang),
                    trainer_lang=tr.language or 'ru',
                    notifications_enabled=tr.notifications_enabled,
                )
                if sent:
                    trainer_ud = context.application.user_data.get(tr.telegram_id)
                    if isinstance(trainer_ud, dict):
                        trainer_ud.pop('nav_message_id', None)
                        trainer_ud['current_screen'] = None

            # Возвращаемся к списку записей
            context.user_data['temp_callback_data'] = 'my_bookings'
            await show_my_bookings(update, context)
        else:
            await show_booking_info(update, context)


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать справку (текст зависит от роли)"""
    query = update.callback_query
    if query:
        await query.answer()

    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'

    async with get_session() as session:
        max_per_day = await SettingsRepository(session).get_max_bookings_per_day()

    if user and user.is_admin():
        text = get_text('common.help_admin', lang)
    elif user and user.role == UserRole.TRAINER:
        text = get_text('common.help_trainer', lang)
    else:
        text = get_text('common.help_athlete', lang, max_per_day=max_per_day)

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


async def show_settings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    skip_answer: bool = False,
):
    """Показать меню настроек"""
    query = update.callback_query
    if query and not skip_answer:
        await query.answer()

    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'

    notif_state = (
        get_text('settings.notif_on', lang)
        if user.notifications_enabled
        else get_text('settings.notif_off', lang)
    )
    text = get_text('settings.intro', lang, notif_state=notif_state)
    keyboard = settings_keyboard(lang, notifications_enabled=user.notifications_enabled)

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')


async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вкл/выкл уведомления от бота для текущего пользователя"""
    query = update.callback_query

    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'

    async with get_session() as session:
        user_repo = UserRepository(session)
        db_user = await user_repo.get_by_id(user.id)
        if not db_user:
            await query.answer(get_text('common.user_not_found', lang), show_alert=True)
            return
        db_user.notifications_enabled = not db_user.notifications_enabled
        await session.commit()
        user.notifications_enabled = db_user.notifications_enabled

    msg = (
        get_text('settings.toggled_on', lang)
        if user.notifications_enabled
        else get_text('settings.toggled_off', lang)
    )
    await query.answer(msg, show_alert=True)
    await show_settings(update, context, skip_answer=True)


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

    # Обновляем нижнюю клавиатуру на новый язык и роль
    from src.keyboards.athlete_keyboards import main_reply_keyboard
    role_str = user.ui_role_key()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="👇",
        reply_markup=main_reply_keyboard(lang_code, role_str)
    )

    # Возвращаемся в главное меню
    await show_main_menu(update, context)


async def show_schedule_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать сохранённую картинку расписания"""
    from src.services.schedule_image_service import get_image_path
    from src.keyboards.athlete_keyboards import schedule_days_keyboard

    query = update.callback_query
    await query.answer()

    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    is_trainer_or_admin = user and user.has_trainer_permissions()
    back = 'trainer_menu' if is_trainer_or_admin else 'main_menu'

    image_path = get_image_path()
    if not image_path:
        await query.edit_message_text(
            get_text('admin.image_not_uploaded', lang),
            reply_markup=schedule_days_keyboard(lang, back_callback=back),
            parse_mode='Markdown'
        )
        return

    # Отправляем картинку новым сообщением (без подписи)
    with open(image_path, 'rb') as f:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=f
        )

