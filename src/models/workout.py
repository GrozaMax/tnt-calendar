"""
Модель тренировки
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, select, func, inspect as sa_inspect
from sqlalchemy.orm import Mapped, mapped_column, relationship, column_property
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.hybrid import hybrid_property

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.booking import Booking


class Workout(Base, TimestampMixin):
    """Модель тренировки"""
    __tablename__ = 'workouts'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    datetime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True
    )
    duration: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
        comment="Длительность в минутах"
    )
    max_participants: Mapped[int] = mapped_column(
        Integer,
        default=999,
        nullable=False
    )
    trainer_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('users.id'),
        nullable=True
    )
    
    # Relationships
    trainer: Mapped["User"] = relationship(
        "User",
        back_populates="workouts",
        foreign_keys=[trainer_id]
    )
    bookings: Mapped[List["Booking"]] = relationship(
        "Booking",
        back_populates="workout",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return (
            f"<Workout(id={self.id}, name='{self.name}', "
            f"datetime={self.datetime.strftime('%Y-%m-%d %H:%M')})>"
        )
    
    @hybrid_property
    def current_participants(self) -> int:
        """
        Текущее количество участников
        
        Использует hybrid property для поддержки как Python, так и SQL выражений.
        Считает по загруженной коллекции bookings (selectinload), без lazy load —
        иначе в async-сессии будет ошибка.
        """
        try:
            try:
                inst = sa_inspect(self)
            except Exception:
                return 0
            if inst is None:
                return 0
            # Пока связь не подгружена — не обращаемся к self.bookings
            if "bookings" in inst.unloaded:
                return 0
            return len([b for b in self.bookings if b.is_active])
        except Exception:
            return 0
    
    @current_participants.expression
    @classmethod
    def current_participants(cls):
        """SQL выражение для подсчета участников"""
        from src.models.booking import Booking, BookingStatus
        return (
            select(func.count(Booking.id))
            .where(
                Booking.workout_id == cls.id,
                Booking.status == BookingStatus.ACTIVE
            )
            .correlate_except(Booking)
            .scalar_subquery()
        )
    
    @property
    def has_free_slots(self) -> bool:
        """Проверка наличия свободных мест"""
        return self.current_participants < self.max_participants
    
    @property
    def is_full(self) -> bool:
        """Проверка, заполнена ли тренировка"""
        return self.current_participants >= self.max_participants
    
    def get_participants_count(self) -> str:
        """Форматированное количество участников"""
        return f"{self.current_participants}/{self.max_participants}"
    
    async def get_current_participants_async(self, session: AsyncSession) -> int:
        """
        Асинхронное получение количества текущих участников
        
        Args:
            session: SQLAlchemy async session
            
        Returns:
            Количество активных записей
        """
        from src.models.booking import Booking, BookingStatus
        
        result = await session.execute(
            select(func.count(Booking.id))
            .where(
                Booking.workout_id == self.id,
                Booking.status == BookingStatus.ACTIVE
            )
        )
        return result.scalar() or 0

