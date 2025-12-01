"""
Декораторы для проверки прав доступа
"""
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from src.models import UserRole
from src.database import get_session
from src.database.repositories import UserRepository


def role_required(*required_roles: UserRole):
    """
    Декоратор для проверки роли пользователя.
    
    Args:
        *required_roles: Список ролей, которым разрешён доступ
    
    Example:
        @role_required(UserRole.TRAINER, UserRole.ADMIN)
        async def trainer_handler(update, context):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            telegram_id = update.effective_user.id
            
            async with get_session() as session:
                user_repo = UserRepository(session)
                user = await user_repo.get_by_telegram_id(telegram_id)
                
                if not user:
                    await update.effective_message.reply_text(
                        "❌ Пользователь не найден. Используйте /start"
                    )
                    return
                
                if user.role not in required_roles:
                    await update.effective_message.reply_text(
                        "❌ У вас нет прав для выполнения этой команды."
                    )
                    return
                
                # Сохраняем пользователя в контекст для использования в обработчике
                context.user_data['current_user'] = user
                return await func(update, context)
        
        return wrapper
    return decorator


def ensure_user_exists(func):
    """
    Декоратор для автоматического создания пользователя, если он не существует.
    Также сохраняет пользователя в context.user_data['current_user']
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_user = update.effective_user
        
        async with get_session() as session:
            user_repo = UserRepository(session)
            user, created = await user_repo.get_or_create(
                telegram_id=telegram_user.id,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                username=telegram_user.username,
                language='ru'  # По умолчанию русский
            )
            
            if created:
                await session.commit()
            
            # Сохраняем пользователя в контекст
            context.user_data['current_user'] = user
            return await func(update, context)
    
    return wrapper

