"""
Обработчики для администраторов
"""
from datetime import date, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.database import get_session
from src.database.repositories import WorkoutRepository, UserRepository, BookingRepository
from src.locales import get_text
from src.models import User, UserRole, BookingStatus
from src.services.notification_service import notify_athlete_workout_cancelled
from src.utils.decorators import role_required


def _build_admin_menu_content(lang: str = 'ru'):
    """Возвращает (text, keyboard) для панели администратора — используется из callback и text handler."""
    text = (
        f"{get_text('admin.panel_title', lang)}\n\n"
        f"{get_text('admin.panel_desc', lang)}"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text('admin.schedule_today', lang), callback_data='admin_view_workouts:today')],
        [InlineKeyboardButton(get_text('admin.schedule_tomorrow', lang), callback_data='admin_view_workouts:tomorrow')],
        [InlineKeyboardButton(get_text('admin.schedule_week', lang), callback_data='admin_view_workouts:week')],
        [InlineKeyboardButton(get_text('admin.users_stats', lang), callback_data='admin_users_stats')],
        [InlineKeyboardButton(get_text('admin.schedule_image', lang), callback_data='admin_schedule_image')],
        [InlineKeyboardButton(get_text('menu.back', lang), callback_data='main_menu')],
    ])
    return text, keyboard


@role_required(UserRole.ADMIN)
async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню администратора (только просмотр)"""
    query = update.callback_query
    await query.answer()
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    text, keyboard = _build_admin_menu_content(lang)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')


@role_required(UserRole.ADMIN)
async def show_admin_workouts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать расписание (для просмотра)"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    # Получаем период из callback_data
    _, period = query.data.split(':')
    
    if period == 'today':
        target_date = date.today()
        date_end = target_date
        title = get_text('schedule.today', lang)
    elif period == 'tomorrow':
        target_date = date.today() + timedelta(days=1)
        date_end = target_date
        title = get_text('schedule.tomorrow', lang)
    else:  # week — показываем выбор дня
        from src.keyboards.athlete_keyboards import WEEKDAY_NAMES
        today = date.today()
        day_names = WEEKDAY_NAMES.get(lang, WEEKDAY_NAMES['ru'])
        text = get_text('admin.week_select_day', lang)
        keyboard = []
        for i in range(7):
            d = today + timedelta(days=i)
            label = f"{'📍 ' if i == 0 else ''}{day_names[d.weekday()]} {d.strftime('%d.%m')}"
            keyboard.append([InlineKeyboardButton(label, callback_data=f'admin_day:{d.isoformat()}')])
        keyboard.append([InlineKeyboardButton(get_text('menu.back', lang), callback_data='admin_menu')])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        workouts = await workout_repo.get_by_date_range(target_date, date_end)

    back_btn = [[InlineKeyboardButton(get_text('menu.back', lang), callback_data='admin_menu')]]

    if not workouts:
        await query.edit_message_text(
            f"📅 *{title}*\n\n{get_text('admin.no_workouts_found', lang)}",
            reply_markup=InlineKeyboardMarkup(back_btn),
            parse_mode='Markdown'
        )
        return

    text = get_text('admin.schedule_title', lang, title=title, count=len(workouts)) + "\n\n"
    keyboard = []

    for workout in workouts[:20]:
        occupancy = workout.current_participants / workout.max_participants
        status = "🔴" if occupancy >= 1.0 else ("🟡" if occupancy >= 0.8 else "🟢")
        button_text = (
            f"{status} {workout.datetime.strftime('%d.%m %H:%M')} - {workout.name} "
            f"({workout.current_participants}/{workout.max_participants})"
        )
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'admin_workout_details:{workout.id}:{period}')])

    if len(workouts) > 20:
        text += get_text('admin.shown_first', lang, count=len(workouts)) + "\n"

    keyboard += back_btn

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


@role_required(UserRole.ADMIN)
async def show_admin_day_workouts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать расписание за конкретный день (из недельного выбора)"""
    query = update.callback_query
    await query.answer()

    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'

    day_str = query.data.split(':')[1]
    target_date = date.fromisoformat(day_str)

    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        workouts = await workout_repo.get_by_date_range(target_date, target_date)

    day_label = target_date.strftime('%d.%m.%Y')
    back_btn = [[InlineKeyboardButton(get_text('admin.back_to_week', lang), callback_data='admin_view_workouts:week')]]

    if not workouts:
        await query.edit_message_text(
            f"📅 *{day_label}*\n\n{get_text('admin.no_workouts_day', lang)}",
            reply_markup=InlineKeyboardMarkup(back_btn),
            parse_mode='Markdown'
        )
        return

    text = f"📅 *{day_label}* — {get_text('admin.workouts_count', lang, count=len(workouts))}\n\n"
    keyboard = []
    for workout in workouts:
        occupancy = workout.current_participants / workout.max_participants
        status = "🔴" if occupancy >= 1.0 else ("🟡" if occupancy >= 0.8 else "🟢")
        button_text = (
            f"{status} {workout.datetime.strftime('%H:%M')} {workout.name} "
            f"({workout.current_participants}/{workout.max_participants})"
        )
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'admin_workout_details:{workout.id}:{day_str}')])

    keyboard += back_btn
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


@role_required(UserRole.ADMIN)
async def show_workout_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать детали тренировки с участниками"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    # Получаем ID тренировки и источник навигации (today/tomorrow/YYYY-MM-DD)
    parts = query.data.split(':')
    workout_id = int(parts[1])
    source = parts[2] if len(parts) > 2 else 'today'
    if source in ('today', 'tomorrow'):
        back_callback = f'admin_view_workouts:{source}'
    else:
        back_callback = f'admin_day:{source}'
    context.user_data['admin_workout_source'] = source
    
    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        booking_repo = BookingRepository(session)
        
        workout = await workout_repo.get_by_id(workout_id, load_relations=True)
        
        if not workout:
            await query.answer(get_text('schedule.workout_not_found', lang), show_alert=True)
            return
        
        text = f"📋 *{workout.name}*\n\n"
        text += f"🕐 {workout.datetime.strftime('%d.%m.%Y %H:%M')}\n"
        text += get_text('schedule.duration', lang, duration=workout.duration) + "\n"
        trainer_name = workout.trainer.full_name if workout.trainer else get_text('schedule.no_trainer', lang)
        text += get_text('schedule.trainer', lang, name=trainer_name) + "\n"
        text += get_text('schedule.participants', lang, count=workout.current_participants, max=workout.max_participants) + "\n"
        
        if workout.description:
            text += f"\n📝 {workout.description}\n"
        
        # Получаем список участников
        bookings = await booking_repo.get_workout_bookings(
            workout_id,
            status=BookingStatus.ACTIVE,
            load_relations=True
        )
        
        if bookings:
            text += f"\n{get_text('admin.participants_list', lang)}\n\n"
            for i, booking in enumerate(bookings[:20], 1):
                text += f"{i}. {booking.user.full_name}"
                if booking.user.username:
                    text += f" (@{booking.user.username})"
                text += "\n"
            
            if len(bookings) > 20:
                text += f"\n{get_text('admin.and_more', lang, count=len(bookings) - 20)}"
        else:
            text += f"\n{get_text('admin.no_participants', lang)}"
        
        keyboard = [
            [
                InlineKeyboardButton(get_text('admin.assign_trainer', lang), callback_data=f'admin_select_trainer:{workout_id}:{source}'),
                InlineKeyboardButton(get_text('admin.delete_workout', lang), callback_data=f'admin_delete_workout_confirm:{workout_id}'),
            ],
            [InlineKeyboardButton(get_text('menu.back', lang), callback_data=back_callback)]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )


@role_required(UserRole.ADMIN)
async def show_users_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику пользователей"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    async with get_session() as session:
        from sqlalchemy import func, select
        from src.models import User as UserModel
        
        # Подсчёт пользователей по ролям
        result = await session.execute(
            select(UserModel.role, func.count(UserModel.id))
            .group_by(UserModel.role)
        )
        
        stats = {role.value: 0 for role in UserRole}
        for role, count in result:
            stats[role.value] = count
        
        # Общее количество
        total = await session.execute(select(func.count(UserModel.id)))
        total_count = total.scalar()
    
    text = f"{get_text('admin.stats_title', lang)}\n\n"
    text += get_text('admin.stats_total', lang, count=total_count) + "\n\n"
    text += get_text('admin.stats_athletes', lang, count=stats.get('athlete', 0)) + "\n"
    text += get_text('admin.stats_trainers', lang, count=stats.get('trainer', 0)) + "\n"
    text += get_text('admin.stats_admins', lang, count=stats.get('admin', 0)) + "\n\n"
    text += get_text('admin.stats_hint', lang)

    keyboard = [[InlineKeyboardButton(get_text('menu.back', lang), callback_data='admin_menu')]]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


@role_required(UserRole.ADMIN)
async def admin_delete_workout_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запросить ввод причины отмены тренировки"""
    query = update.callback_query
    await query.answer()

    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'

    workout_id = int(query.data.split(':')[1])

    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        workout = await workout_repo.get_by_id(workout_id)

    if not workout:
        await query.answer(get_text('schedule.workout_not_found', lang), show_alert=True)
        return

    # Сохраняем ID тренировки и сообщения — ждём текстового сообщения с причиной
    context.user_data['pending_delete_workout_id'] = workout_id
    context.user_data['pending_delete_workout_name'] = workout.name
    context.user_data['pending_delete_workout_dt'] = workout.datetime.strftime('%d.%m.%Y %H:%M')
    context.user_data['pending_delete_message_id'] = query.message.message_id
    context.user_data['pending_delete_chat_id'] = query.message.chat_id

    text = (
        f"{get_text('admin.delete_confirm', lang)}\n\n"
        f"*{workout.name}*\n"
        f"📅 {workout.datetime.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"{get_text('admin.delete_enter_reason', lang)}\n\n"
        f"{get_text('admin.delete_hint', lang)}"
    )
    keyboard = [[InlineKeyboardButton(get_text('admin.delete_cancel', lang), callback_data=f'admin_cancel_delete:{workout_id}')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


@role_required(UserRole.ADMIN)
async def admin_cancel_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменить удаление тренировки"""
    query = update.callback_query
    await query.answer()

    context.user_data.pop('pending_delete_workout_id', None)
    context.user_data.pop('pending_delete_workout_name', None)
    context.user_data.pop('pending_delete_workout_dt', None)

    workout_id = int(query.data.split(':')[1])
    source = context.user_data.get('admin_workout_source', 'today')
    query.data = f'admin_workout_details:{workout_id}:{source}'
    await show_workout_details(update, context)


async def handle_admin_delete_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Принять текст причины и удалить тренировку"""
    workout_id = context.user_data.get('pending_delete_workout_id')
    if not workout_id:
        return  # не ждём ввода — игнорируем

    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'

    reason = update.message.text.strip()
    workout_name = context.user_data.pop('pending_delete_workout_name', '')
    workout_dt = context.user_data.pop('pending_delete_workout_dt', '')
    confirm_message_id = context.user_data.pop('pending_delete_message_id', None)
    confirm_chat_id = context.user_data.pop('pending_delete_chat_id', None)
    context.user_data.pop('pending_delete_workout_id', None)

    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        booking_repo = BookingRepository(session)

        workout = await workout_repo.get_by_id(workout_id, load_relations=True)
        if not workout:
            await update.message.reply_text(get_text('admin.delete_not_found', lang))
            return

        active_bookings = await booking_repo.get_workout_bookings(
            workout_id, status=BookingStatus.ACTIVE, load_relations=True
        )
        athlete_users = [
            {
                'telegram_id': b.user.telegram_id,
                'language': b.user.language or 'ru',
                'notifications_enabled': b.user.notifications_enabled,
            }
            for b in active_bookings if b.user and b.user.telegram_id
        ]

        success = await workout_repo.delete(workout_id)
        if not success:
            await update.message.reply_text(get_text('admin.delete_error', lang))
            return
        await session.commit()

    for athlete in athlete_users:
        await notify_athlete_workout_cancelled(
            bot=context.bot,
            athlete_telegram_id=athlete['telegram_id'],
            workout_name=workout_name,
            workout_datetime=workout_dt,
            reason=reason,
            athlete_lang=athlete['language'],
            notifications_enabled=athlete['notifications_enabled'],
        )

    # Удаляем сообщение с причиной от администратора
    try:
        await update.message.delete()
    except Exception:
        pass

    # Заменяем "Удалить тренировку?" на "Тренировка удалена"
    reason_text = f"\n{get_text('admin.delete_reason', lang, reason=reason)}" if reason else ""
    done_text = (
        f"{get_text('admin.delete_done', lang)}\n\n"
        f"*{workout_name}*\n"
        f"📅 {workout_dt}"
        f"{reason_text}\n\n"
        f"{get_text('admin.notified_athletes', lang, count=len(athlete_users))}"
    )
    if confirm_message_id and confirm_chat_id:
        try:
            await context.bot.edit_message_text(
                chat_id=confirm_chat_id,
                message_id=confirm_message_id,
                text=done_text,
                reply_markup=None,
                parse_mode='Markdown'
            )
        except Exception:
            pass


@role_required(UserRole.ADMIN)
async def admin_delete_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка — удаление теперь обрабатывается через handle_admin_delete_reason"""
    pass


@role_required(UserRole.ADMIN)
async def admin_select_trainer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список тренеров для назначения"""
    query = update.callback_query
    await query.answer()

    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'

    parts = query.data.split(':')
    workout_id = int(parts[1])
    source = parts[2] if len(parts) > 2 else context.user_data.get('admin_workout_source', 'today')

    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        user_repo = UserRepository(session)

        workout = await workout_repo.get_by_id(workout_id, load_relations=True)
        if not workout:
            await query.answer(get_text('schedule.workout_not_found', lang), show_alert=True)
            return

        trainers = await user_repo.get_all_trainers()

    current = get_text('admin.trainer_current', lang, name=workout.trainer.full_name) if workout.trainer else get_text('admin.trainer_none', lang)
    text = get_text('admin.select_trainer', lang, name=workout.name, datetime=workout.datetime.strftime('%d.%m %H:%M'), current=current)

    keyboard = []
    for t in trainers:
        role_label = " 👑" if t.role == UserRole.ADMIN else ""
        keyboard.append([
            InlineKeyboardButton(
                f"{t.full_name}{role_label}",
                callback_data=f'admin_assign_trainer:{workout_id}:{t.id}:{source}'
            )
        ])
    keyboard.append([InlineKeyboardButton(get_text('admin.no_trainer_btn', lang), callback_data=f'admin_assign_trainer:{workout_id}:0:{source}')])
    keyboard.append([InlineKeyboardButton(get_text('menu.back', lang), callback_data=f'admin_workout_details:{workout_id}:{source}')])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


@role_required(UserRole.ADMIN)
async def admin_assign_trainer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Назначить тренера на тренировку"""
    query = update.callback_query
    await query.answer()

    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'

    parts = query.data.split(':')
    workout_id = int(parts[1])
    trainer_id = int(parts[2])
    source = parts[3] if len(parts) > 3 else context.user_data.get('admin_workout_source', 'today')

    async with get_session() as session:
        workout_repo = WorkoutRepository(session)

        trainer_id_value = trainer_id if trainer_id != 0 else None
        workout = await workout_repo.update(workout_id, trainer_id=trainer_id_value)
        if not workout:
            await query.answer(get_text('schedule.workout_not_found', lang), show_alert=True)
            return
        await session.commit()

        # Перечитываем со связями для отображения имени
        workout = await workout_repo.get_by_id(workout_id, load_relations=True)

    trainer_name = workout.trainer.full_name if workout.trainer else get_text('schedule.no_trainer', lang)
    text = get_text('admin.trainer_assigned', lang, name=trainer_name, workout=workout.name, datetime=workout.datetime.strftime('%d.%m.%Y %H:%M'))
    keyboard = [[InlineKeyboardButton(get_text('admin.to_workout', lang), callback_data=f'admin_workout_details:{workout_id}:{source}')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


@role_required(UserRole.ADMIN)
async def show_admin_schedule_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статус картинки расписания и кнопки управления"""
    from src.services.schedule_image_service import image_exists
    query = update.callback_query
    await query.answer()

    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'

    exists = image_exists()
    status_text = get_text('admin.image_loaded', lang) if exists else get_text('admin.image_not_loaded', lang)

    text = f"{get_text('admin.image_title', lang)}\n\n{status_text}\n\n{get_text('admin.image_upload_hint', lang)}"
    keyboard = [
        [InlineKeyboardButton(get_text('admin.image_upload_btn', lang), callback_data='admin_upload_schedule_image')],
    ]
    if exists:
        keyboard.append([InlineKeyboardButton(get_text('admin.image_delete_btn', lang), callback_data='admin_delete_schedule_image')])
    keyboard.append([InlineKeyboardButton(get_text('menu.back', lang), callback_data='admin_menu')])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


@role_required(UserRole.ADMIN)
async def admin_upload_schedule_image_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подготовить бота к приёму фото от администратора"""
    query = update.callback_query
    await query.answer()

    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'

    context.user_data['awaiting_schedule_image'] = True
    await query.edit_message_text(
        get_text('admin.image_upload_prompt', lang),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(get_text('admin.image_cancel', lang), callback_data='admin_schedule_image')]
        ]),
        parse_mode='Markdown'
    )


@role_required(UserRole.ADMIN)
async def admin_delete_schedule_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить текущую картинку расписания"""
    from src.services.schedule_image_service import delete_image
    query = update.callback_query
    await query.answer()

    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'

    delete_image()
    await query.edit_message_text(
        get_text('admin.image_deleted', lang),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(get_text('menu.back', lang), callback_data='admin_schedule_image')]
        ]),
        parse_mode='Markdown'
    )


async def handle_admin_photo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработать фото от администратора (загрузка картинки расписания)"""
    from src.services.schedule_image_service import save_image
    from src.models import UserRole

    if not context.user_data.get('awaiting_schedule_image'):
        return

    user: User = context.user_data.get('current_user')
    if not user or user.role != UserRole.ADMIN:
        return

    lang = user.language if user else 'ru'
    context.user_data['awaiting_schedule_image'] = False

    photo = update.message.photo[-1]  # наибольшее разрешение
    file = await context.bot.get_file(photo.file_id)
    file_bytes = await file.download_as_bytearray()

    # Определяем расширение (Telegram photos — всегда jpeg)
    save_image(bytes(file_bytes), extension="jpg")

    await update.message.reply_text(
        get_text('admin.image_uploaded', lang),
        parse_mode='Markdown'
    )
