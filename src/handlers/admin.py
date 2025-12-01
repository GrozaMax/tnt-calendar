"""
Обработчики для администраторов
"""
from datetime import date, timedelta, datetime
from telegram import Update
from telegram.ext import ContextTypes

from src.database import get_session
from src.database.repositories import WorkoutRepository, UserRepository
from src.keyboards.admin_keyboards import (
    admin_main_menu_keyboard,
    create_schedule_options_keyboard,
    manage_workouts_keyboard,
    workouts_date_selection_keyboard,
    workout_actions_keyboard,
    confirm_delete_keyboard,
    manage_users_keyboard,
    users_list_keyboard,
    user_actions_keyboard,
    back_to_admin_menu_keyboard
)
from src.locales import get_text
from src.models import User, UserRole
from src.utils.decorators import role_required


# Импортируем расписание из скрипта
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from create_weekly_schedule import WEEKLY_SCHEDULE


@role_required(UserRole.ADMIN)
async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню администратора"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    text = "👑 *Панель администратора*\n\n"
    text += "Выберите действие:"
    
    keyboard = admin_main_menu_keyboard(lang)
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


@role_required(UserRole.ADMIN)
async def show_create_schedule_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать варианты создания расписания"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    text = "📅 *Создание расписания*\n\n"
    text += "На сколько недель вперед создать расписание?"
    
    keyboard = create_schedule_options_keyboard(lang)
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


@role_required(UserRole.ADMIN)
async def create_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создать расписание на N недель"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    # Получаем количество недель из callback_data
    _, weeks_str = query.data.split(':')
    weeks = int(weeks_str)
    
    # Показываем процесс
    await query.edit_message_text(
        f"⏳ Создаю расписание на {weeks} недель...",
        parse_mode='Markdown'
    )
    
    async with get_session() as session:
        user_repo = UserRepository(session)
        workout_repo = WorkoutRepository(session)
        
        # Получаем тренера
        trainers = await user_repo.get_all_trainers()
        if not trainers:
            await query.edit_message_text(
                "❌ Не найдено ни одного тренера!\n\n"
                "Назначьте хотя бы одного пользователя тренером.",
                reply_markup=back_to_admin_menu_keyboard(lang)
            )
            return
        
        trainer = trainers[0]
        start_date = datetime.now().date()
        
        total_created = 0
        total_skipped = 0
        
        # Создаём расписание
        for week in range(weeks):
            for days_offset in range(7):
                current_date = start_date + timedelta(days=week * 7 + days_offset)
                weekday = current_date.weekday()
                
                if current_date < datetime.now().date():
                    continue
                
                day_schedule = WEEKLY_SCHEDULE.get(weekday, [])
                
                for slot in day_schedule:
                    hour, minute = map(int, slot["time"].split(":"))
                    workout_datetime = datetime.combine(current_date, datetime.min.time())
                    workout_datetime = workout_datetime.replace(hour=hour, minute=minute)
                    
                    # Проверяем существование
                    existing = await workout_repo.get_by_date(current_date)
                    exists = any(
                        w.datetime == workout_datetime and w.name == slot["name"]
                        for w in existing
                    )
                    
                    if exists:
                        total_skipped += 1
                        continue
                    
                    # Создаём
                    await workout_repo.create(
                        name=slot["name"],
                        datetime=workout_datetime,
                        trainer_id=trainer.id,
                        duration=slot["duration"],
                        max_participants=slot["max_participants"]
                    )
                    total_created += 1
        
        await session.commit()
    
    # Результат
    text = "🎉 *Расписание создано!*\n\n"
    text += f"✅ Создано тренировок: *{total_created}*\n"
    text += f"⚠️ Пропущено (уже существуют): *{total_skipped}*\n"
    text += f"📅 Недель: *{weeks}*"
    
    await query.edit_message_text(
        text,
        reply_markup=back_to_admin_menu_keyboard(lang),
        parse_mode='Markdown'
    )


@role_required(UserRole.ADMIN)
async def show_manage_workouts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню управления тренировками"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    text = "📋 *Управление тренировками*\n\n"
    text += "Выберите действие:"
    
    keyboard = manage_workouts_keyboard(lang)
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


@role_required(UserRole.ADMIN)
async def list_workouts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список тренировок"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    text = "📋 *Список тренировок*\n\n"
    text += "Выберите период:"
    
    keyboard = workouts_date_selection_keyboard(lang)
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


@role_required(UserRole.ADMIN)
async def show_workouts_by_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать тренировки за выбранную дату"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    # Получаем период из callback_data
    _, period = query.data.split(':')
    
    if period == 'today':
        target_date = date.today()
        title = "Сегодня"
    elif period == 'tomorrow':
        target_date = date.today() + timedelta(days=1)
        title = "Завтра"
    else:  # week
        # Показываем все тренировки на неделю
        await show_week_workouts(query, user, lang)
        return
    
    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        workouts = await workout_repo.get_by_date(target_date, load_relations=True)
    
    if not workouts:
        text = f"📅 *{title}* ({target_date.strftime('%d.%m.%Y')})\n\n"
        text += "❌ Тренировок не найдено"
        
        await query.edit_message_text(
            text,
            reply_markup=back_to_admin_menu_keyboard(lang),
            parse_mode='Markdown'
        )
        return
    
    text = f"📅 *{title}* ({target_date.strftime('%d.%m.%Y')})\n\n"
    text += f"Найдено тренировок: *{len(workouts)}*\n"
    text += "Нажмите на тренировку для управления:\n\n"
    
    # Создаём кнопки для каждой тренировки
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = []
    
    for workout in workouts[:20]:  # Ограничение в 20 тренировок
        button_text = (
            f"🕐 {workout.datetime.strftime('%H:%M')} - {workout.name} "
            f"({workout.current_participants}/{workout.max_participants})"
        )
        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f'admin_workout_info:{workout.id}'
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            get_text('menu.back', lang),
            callback_data='admin_list_workouts'
        )
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def show_week_workouts(query, user, lang):
    """Показать статистику за неделю"""
    today = date.today()
    week_end = today + timedelta(days=7)
    
    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        workouts = await workout_repo.get_by_date_range(today, week_end)
    
    text = f"📅 *Эта неделя*\n\n"
    text += f"Период: {today.strftime('%d.%m')} - {week_end.strftime('%d.%m.%Y')}\n"
    text += f"Всего тренировок: *{len(workouts)}*\n\n"
    
    # Группируем по дням
    by_date = {}
    for workout in workouts:
        d = workout.datetime.date()
        if d not in by_date:
            by_date[d] = []
        by_date[d].append(workout)
    
    for d in sorted(by_date.keys())[:7]:
        day_workouts = by_date[d]
        weekday = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][d.weekday()]
        text += f"*{weekday} {d.strftime('%d.%m')}*: {len(day_workouts)} тренировок\n"
    
    await query.edit_message_text(
        text,
        reply_markup=back_to_admin_menu_keyboard(lang),
        parse_mode='Markdown'
    )


@role_required(UserRole.ADMIN)
async def show_manage_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню управления пользователями"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    text = "👥 *Управление пользователями*\n\n"
    text += "Выберите действие:"
    
    keyboard = manage_users_keyboard(lang)
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


@role_required(UserRole.ADMIN)
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список пользователей"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    async with get_session() as session:
        user_repo = UserRepository(session)
        # Получаем всех пользователей (нужно добавить метод)
        result = await session.execute(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT 20"
        )
        # Временно используем простой запрос
        from sqlalchemy import select as sql_select
        from src.models import User as UserModel
        result = await session.execute(
            sql_select(UserModel).order_by(UserModel.created_at.desc()).limit(20)
        )
        users = list(result.scalars().all())
    
    if not users:
        text = "👥 Пользователи не найдены"
        await query.edit_message_text(
            text,
            reply_markup=back_to_admin_menu_keyboard(lang)
        )
        return
    
    text = f"👥 *Пользователи* (всего: {len(users)})\n\n"
    text += "Выберите пользователя:"
    
    keyboard = users_list_keyboard(users, lang)
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


@role_required(UserRole.ADMIN)
async def show_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о пользователе"""
    query = update.callback_query
    await query.answer()
    
    current_user: User = context.user_data.get('current_user')
    lang = current_user.language if current_user else 'ru'
    
    # Получаем ID пользователя
    _, user_id = query.data.split(':')
    user_id = int(user_id)
    
    async with get_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id)
        
        if not user:
            await query.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        role_emoji = {
            "athlete": "🏋️",
            "trainer": "🤸‍♀️",
            "admin": "👑"
        }.get(user.role.value, "👤")
        
        text = f"👤 *Информация о пользователе*\n\n"
        text += f"{role_emoji} *{user.full_name}*\n\n"
        text += f"Роль: {user.role.value}\n"
        text += f"Telegram ID: `{user.telegram_id}`\n"
        if user.username:
            text += f"Username: @{user.username}\n"
        text += f"Язык: {user.language}\n"
        text += f"Создан: {user.created_at.strftime('%d.%m.%Y')}"
        
        keyboard = user_actions_keyboard(user.id, user.role.value, lang)
        
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )


@role_required(UserRole.ADMIN)
async def set_user_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Изменить роль пользователя"""
    query = update.callback_query
    await query.answer()
    
    current_user: User = context.user_data.get('current_user')
    lang = current_user.language if current_user else 'ru'
    
    # Парсим callback_data
    _, user_id, new_role = query.data.split(':')
    user_id = int(user_id)
    
    async with get_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id)
        
        if not user:
            await query.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        # Изменяем роль
        old_role = user.role.value
        user.role = UserRole.TRAINER if new_role == 'trainer' else UserRole.ATHLETE
        await session.commit()
    
    role_text = "🤸‍♀️ Тренером" if new_role == 'trainer' else "🏋️ Атлетом"
    await query.answer(f"✅ Пользователь назначен {role_text}", show_alert=True)
    
    # Обновляем информацию
    await show_user_info(update, context)


@role_required(UserRole.ADMIN)
async def show_workout_info_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о тренировке (для админа)"""
    query = update.callback_query
    await query.answer()
    
    current_user: User = context.user_data.get('current_user')
    lang = current_user.language if current_user else 'ru'
    
    # Получаем ID тренировки
    _, workout_id = query.data.split(':')
    workout_id = int(workout_id)
    
    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        workout = await workout_repo.get_by_id(workout_id, load_relations=True)
        
        if not workout:
            await query.answer("❌ Тренировка не найдена", show_alert=True)
            return
        
        text = f"📋 *{workout.name}*\n\n"
        text += f"🕐 {workout.datetime.strftime('%d.%m.%Y %H:%M')}\n"
        text += f"⏱ {workout.duration} мин\n"
        text += f"👤 Тренер: {workout.trainer.full_name}\n"
        text += f"👥 Записалось: {workout.current_participants}/{workout.max_participants}\n"
        
        if workout.description:
            text += f"\n📝 {workout.description}"
        
        keyboard = workout_actions_keyboard(workout_id, lang)
        
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )


@role_required(UserRole.ADMIN)
async def confirm_delete_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать подтверждение удаления тренировки"""
    query = update.callback_query
    await query.answer()
    
    current_user: User = context.user_data.get('current_user')
    lang = current_user.language if current_user else 'ru'
    
    # Получаем ID тренировки
    _, workout_id = query.data.split(':')
    workout_id = int(workout_id)
    
    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        workout = await workout_repo.get_by_id(workout_id, load_relations=True)
        
        if not workout:
            await query.answer("❌ Тренировка не найдена", show_alert=True)
            return
        
        text = f"⚠️ *Подтверждение удаления*\n\n"
        text += f"Вы уверены, что хотите удалить тренировку?\n\n"
        text += f"📋 {workout.name}\n"
        text += f"🕐 {workout.datetime.strftime('%d.%m.%Y %H:%M')}\n"
        text += f"👥 Записано участников: {workout.current_participants}\n\n"
        
        if workout.current_participants > 0:
            text += f"⚠️ *Внимание!* У тренировки есть записавшиеся участники!\n"
            text += f"Их записи будут удалены."
        
        keyboard = confirm_delete_keyboard(workout_id, lang)
        
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )


@role_required(UserRole.ADMIN)
async def show_workout_participants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список участников тренировки"""
    query = update.callback_query
    await query.answer()
    
    current_user: User = context.user_data.get('current_user')
    lang = current_user.language if current_user else 'ru'
    
    # Получаем ID тренировки
    _, workout_id = query.data.split(':')
    workout_id = int(workout_id)
    
    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        from src.database.repositories import BookingRepository
        booking_repo = BookingRepository(session)
        
        workout = await workout_repo.get_by_id(workout_id, load_relations=True)
        
        if not workout:
            await query.answer("❌ Тренировка не найдена", show_alert=True)
            return
        
        # Получаем активные записи
        from src.models import BookingStatus
        bookings = await booking_repo.get_workout_bookings(workout_id, status=BookingStatus.ACTIVE, load_relations=True)
        
        text = f"👥 *Участники тренировки*\n\n"
        text += f"📋 {workout.name}\n"
        text += f"🕐 {workout.datetime.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        if not bookings:
            text += "ℹ️ Пока никто не записался"
        else:
            text += f"Записалось: *{len(bookings)}/{workout.max_participants}*\n\n"
            for i, booking in enumerate(bookings, 1):
                text += f"{i}. {booking.user.full_name}"
                if booking.user.username:
                    text += f" (@{booking.user.username})"
                text += "\n"
        
        keyboard = workout_actions_keyboard(workout_id, lang)
        
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )


@role_required(UserRole.ADMIN)
async def delete_workout_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить тренировку после подтверждения"""
    query = update.callback_query
    await query.answer()
    
    current_user: User = context.user_data.get('current_user')
    lang = current_user.language if current_user else 'ru'
    
    # Получаем ID тренировки
    _, workout_id = query.data.split(':')
    workout_id = int(workout_id)
    
    import logging
    logger = logging.getLogger(__name__)
    
    # Сохраняем данные о тренировке
    workout_name = ""
    workout_date = ""
    participants_count = 0
    
    try:
        # Блок работы с БД - весь код БД должен быть ВНУТРИ контекста
        async with get_session() as session:
            workout_repo = WorkoutRepository(session)
            workout = await workout_repo.get_by_id(workout_id, load_relations=True)
            
            if not workout:
                await query.answer("❌ Тренировка не найдена", show_alert=True)
                return
            
            # Сохраняем данные ДО удаления
            workout_name = workout.name
            workout_date = workout.datetime.strftime('%d.%m.%Y %H:%M')
            participants_count = workout.current_participants
            
            # Удаляем тренировку (каскадное удаление удалит и записи)
            success = await workout_repo.delete(workout_id)
            
            if not success:
                await query.answer("❌ Ошибка при удалении", show_alert=True)
                await query.edit_message_text(
                    "❌ Ошибка при удалении тренировки",
                    reply_markup=back_to_admin_menu_keyboard(lang)
                )
                return
            
            logger.info(f"Перед commit: удаляем тренировку {workout_id}")
            
            # ВАЖНО: коммитим изменения в БД
            # После commit НЕ должно быть операций с БД в этом контексте!
            await session.commit()
            
            logger.info(f"После commit: тренировка {workout_id} закоммичена")
        
        # ВАЖНО: весь код UI делаем ПОСЛЕ закрытия сессии!
        # Это гарантирует, что commit применился
        logger.info(f"Сессия закрыта, проверяем удаление в новой сессии")
        
        # Проверка в новой сессии
        async with get_session() as check_session:
            check_repo = WorkoutRepository(check_session)
            check_workout = await check_repo.get_by_id(workout_id)
            if check_workout:
                logger.error(f"КРИТИЧЕСКАЯ ОШИБКА: Тренировка {workout_id} все еще существует!")
                await query.answer("❌ Ошибка: тренировка не удалена из БД", show_alert=True)
                return
            else:
                logger.info(f"✅ Подтверждено: тренировка {workout_id} удалена из БД")
        
        # Успешное удаление - показываем результат
        text = f"✅ *Тренировка удалена*\n\n"
        text += f"📋 {workout_name}\n"
        text += f"🕐 {workout_date}\n"
        
        if participants_count > 0:
            text += f"\n🗑️ Удалено записей участников: {participants_count}"
        
        await query.answer("✅ Тренировка удалена", show_alert=True)
        
        await query.edit_message_text(
            text,
            reply_markup=back_to_admin_menu_keyboard(lang),
            parse_mode='Markdown'
        )
            
    except Exception as e:
        logger.error(f"Ошибка при удалении тренировки {workout_id}: {e}", exc_info=True)
        await query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

