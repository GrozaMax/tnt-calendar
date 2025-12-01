"""
API для управления пользователями
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select

from web.api.auth import get_current_user
from src.database import get_session
from src.database.repositories import UserRepository
from src.models import User, UserRole

router = APIRouter()


class UserResponse(BaseModel):
    """Ответ с информацией о пользователе"""
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    full_name: str
    role: str
    language: str
    created_at: str
    
    class Config:
        from_attributes = True


class UserUpdateRole(BaseModel):
    """Обновление роли пользователя"""
    role: str = Field(..., pattern="^(athlete|trainer|admin)$")


@router.get("/", response_model=List[UserResponse])
async def get_users(
    role: Optional[str] = Query(None, pattern="^(athlete|trainer|admin)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user)
):
    """
    Получить список пользователей
    
    Только для админов.
    """
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view users list"
        )
    
    async with get_session() as session:
        # Строим запрос
        query = select(User).order_by(User.created_at.desc())
        
        # Фильтр по роли
        if role:
            query = query.where(User.role == UserRole(role))
        
        # Пагинация
        query = query.limit(limit).offset(offset)
        
        result = await session.execute(query)
        users = list(result.scalars().all())
        
        return [
            UserResponse(
                id=u.id,
                telegram_id=u.telegram_id,
                username=u.username,
                first_name=u.first_name,
                last_name=u.last_name,
                full_name=u.full_name,
                role=u.role.value,
                language=u.language,
                created_at=u.created_at.isoformat()
            )
            for u in users
        ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Получить информацию о пользователе
    
    Только для админов.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view user details"
        )
    
    async with get_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            role=user.role.value,
            language=user.language,
            created_at=user.created_at.isoformat()
        )


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_data: UserUpdateRole,
    current_user: User = Depends(get_current_user)
):
    """
    Изменить роль пользователя
    
    Только для админов.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can change user roles"
        )
    
    async with get_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Нельзя изменить роль самому себе
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot change your own role"
            )
        
        # Обновляем роль
        user.role = UserRole(role_data.role)
        await session.commit()
        await session.refresh(user)
        
        return UserResponse(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            role=user.role.value,
            language=user.language,
            created_at=user.created_at.isoformat()
        )


@router.get("/stats/summary")
async def get_users_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Получить статистику по пользователям
    
    Только для админов.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view statistics"
        )
    
    async with get_session() as session:
        # Подсчёт пользователей по ролям
        from sqlalchemy import func
        
        result = await session.execute(
            select(User.role, func.count(User.id))
            .group_by(User.role)
        )
        
        stats = {role.value: 0 for role in UserRole}
        for role, count in result:
            stats[role.value] = count
        
        # Общее количество
        total = await session.execute(select(func.count(User.id)))
        total_count = total.scalar()
        
        return {
            "total": total_count,
            "by_role": stats
        }

