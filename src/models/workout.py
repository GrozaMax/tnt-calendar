"""
Модель тренировки
"""
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.booking import Booking


class Workout(Base, TimestampMixin):
    """Модель тренировки"""
    __tablename__ = 'workouts'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    trainer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id'),
        nullable=False
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
    
    @property
    def current_participants(self) -> int:
        """Текущее количество участников"""
        return len([b for b in self.bookings if b.is_active()])
    
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

