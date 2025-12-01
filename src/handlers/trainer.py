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
from src.keyboards.athlete_keyboards import main_menu_keyboard
from src.locales import get_text
from src.models import User, UserRole, BookingStatus
from src.utils.decorators import role_required


@role_required(UserRole.TRAINER)
async def show_trainer_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню тренера"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    text = "🤸‍♀️ *Панель тренера*\n\n"
    text += "Выберите действие:"
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton("📅 Мои тренировки на сегодня", callback_data='trainer_workouts:today')],
        [InlineKeyboardButton("📅 Мои тренировки на завтра", callback_data='trainer_workouts:tomorrow')],
        [InlineKeyboardButton("📅 Мои тренировки на неделю", callback_data='trainer_workouts:week')],
        [InlineKeyboardButton(get_text('menu.back', lang), callback_data='main_menu')]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


@role_required(UserRole.TRAINER)
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
        title = "Сегодня"
    elif period == 'tomorrow':
        target_date = date.today() + timedelta(days=1)
        date_end = target_date
        title = "Завтра"
    else:  # week
        target_date = date.today()
        date_end = target_date + timedelta(days=7)
        title = "На неделю"
    
    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        workouts = await workout_repo.get_by_date_range(
            target_date, 
            date_end,
            load_relations=True
        )
        
        # Фильтруем только тренировки этого тренера
        workouts = [w for w in workouts if w.trainer_id == user.id]
    
    if not workouts:
        text = f"📅 *{title}*\n\n"
        text += "У вас нет запланированных тренировок\n\n"
        text += "💡 Для создания тренировок используйте веб-интерфейс:\n"
        text += "https://your-domain.com"
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [[InlineKeyboardButton("« Назад", callback_data='trainer_menu')]]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return
    
    text = f"📅 *Ваши тренировки: {title}*\n\n"
    text += f"Найдено: *{len(workouts)}*\n\n"
    
    # Создаём кнопки для каждой тренировки
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = []
    
    for workout in workouts[:20]:  # Ограничение в 20
        occupancy = workout.current_participants / workout.max_participants
        
        if occupancy >= 1.0:
            status = "🔴"
        elif occupancy >= 0.8:
            status = "🟡"
        else:
            status = "🟢"
        
        button_text = (
            f"{status} {workout.datetime.strftime('%d.%m %H:%M')} - {workout.name} "
            f"({workout.current_participants}/{workout.max_participants})"
        )
        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f'trainer_workout_info:{workout.id}'
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("« Назад", callback_data='trainer_menu')
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


@role_required(UserRole.TRAINER)
async def show_trainer_workout_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о тренировке (для тренера)"""
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data.get('current_user')
    lang = user.language if user else 'ru'
    
    # Получаем ID тренировки
    _, workout_id = query.data.split(':')
    workout_id = int(workout_id)
    
    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        booking_repo = BookingRepository(session)
        
        workout = await workout_repo.get_by_id(workout_id, load_relations=True)
        
        if not workout:
            await query.answer("❌ Тренировка не найдена", show_alert=True)
            return
        
        # Проверяем, что это тренировка данного тренера
        if workout.trainer_id != user.id:
            await query.answer("❌ Это не ваша тренировка", show_alert=True)
            return
        
        text = f"📋 *{workout.name}*\n\n"
        text += f"🕐 {workout.datetime.strftime('%d.%m.%Y %H:%M')}\n"
        text += f"⏱ {workout.duration} мин\n"
        text += f"👥 Записалось: *{workout.current_participants}/{workout.max_participants}*\n"
        
        if workout.description:
            text += f"\n📝 {workout.description}\n"
        
        # Получаем список участников
        bookings = await booking_repo.get_workout_bookings(
            workout_id,
            status=BookingStatus.ACTIVE,
            load_relations=True
        )
        
        if bookings:
            text += f"\n👥 *Список участников:*\n\n"
            for i, booking in enumerate(bookings[:20], 1):
                text += f"{i}. {booking.user.full_name}"
                if booking.user.username:
                    text += f" (@{booking.user.username})"
                text += "\n"
            
            if len(bookings) > 20:
                text += f"\n... и ещё {len(bookings) - 20}"
        else:
            text += "\nℹ️ Пока никто не записался"
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [[InlineKeyboardButton("« Назад", callback_data='trainer_workouts:today')]]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

