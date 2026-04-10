"""
Репозиторий для работы с пользователями
"""
from __future__ import annotations

from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User, UserRole


class UserRepository:
    """Репозиторий для работы с пользователями"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        return await self.session.get(User, user_id)
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def create(
        self,
        telegram_id: int,
        first_name: str,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        role: UserRole = UserRole.ATHLETE,
        language: str = 'ru'
    ) -> User:
        """Создать нового пользователя"""
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            role=role,
            language=language
        )
        self.session.add(user)
        await self.session.flush()
        return user
    
    async def get_or_create(
        self,
        telegram_id: int,
        first_name: str,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        language: str = 'ru'
    ) -> tuple[User, bool]:
        """
        Получить или создать пользователя.
        
        Returns:
            tuple[User, bool]: (пользователь, создан ли новый)
        """
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            return user, False
        
        user = await self.create(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            language=language
        )
        return user, True
    
    async def update_role(self, user_id: int, role: UserRole) -> Optional[User]:
        """Обновить роль пользователя"""
        user = await self.get_by_id(user_id)
        if user:
            user.role = role
            await self.session.flush()
        return user
    
    async def update_language(self, user_id: int, language: str) -> Optional[User]:
        """Обновить язык пользователя"""
        user = await self.get_by_id(user_id)
        if user:
            user.language = language
            await self.session.flush()
        return user
    
    async def get_all(self) -> list[User]:
        """Получить всех пользователей"""
        result = await self.session.execute(select(User))
        return list(result.scalars().all())
    
    async def get_all_trainers(self) -> list[User]:
        """Получить всех тренеров"""
        result = await self.session.execute(
            select(User).where(
                User.role.in_([UserRole.TRAINER, UserRole.ADMIN])
            )
        )
        return list(result.scalars().all())
    
    async def update(self, user_id: int, data: Dict[str, Any]) -> Optional[User]:
        """Обновить данные пользователя"""
        user = await self.get_by_id(user_id)
        if user:
            for key, value in data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            await self.session.flush()
        return user

