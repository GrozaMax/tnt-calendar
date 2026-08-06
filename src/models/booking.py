"""
Модель записи на тренировку
"""
import enum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, Enum, UniqueConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.workout import Workout


class BookingStatus(enum.Enum):
    """Статусы записи"""
    ACTIVE = "active"
    CANCELLED = "cancelled"


class Booking(Base, TimestampMixin):
    """Модель записи на тренировку"""
    __tablename__ = 'bookings'
    
    __table_args__ = (
        UniqueConstraint('user_id', 'workout_id', name='uq_user_workout'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id'),
        nullable=False,
        index=True
    )
    workout_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('workouts.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus),
        default=BookingStatus.ACTIVE,
        nullable=False
    )
    guests: Mapped[int] = mapped_column(Integer, default=0)
    reminder_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    reminder_message_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=None
    )
    
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="bookings"
    )
    workout: Mapped["Workout"] = relationship(
        "Workout",
        back_populates="bookings"
    )
    
    def __repr__(self) -> str:
        return (
            f"<Booking(id={self.id}, user_id={self.user_id}, "
            f"workout_id={self.workout_id}, status={self.status.value})>"
        )
    
    @property
    def is_active(self) -> bool:
        """Проверка, активна ли запись"""
        return self.status == BookingStatus.ACTIVE
    
    def cancel(self) -> None:
        """Отмена записи"""
        self.status = BookingStatus.CANCELLED
    
    def activate(self) -> None:
        """Активация записи"""
        self.status = BookingStatus.ACTIVE

