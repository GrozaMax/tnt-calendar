"""
Модель пользователя
"""
import enum
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, Enum, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.workout import Workout
    from src.models.booking import Booking


class UserRole(enum.Enum):
    """Роли пользователей"""
    ATHLETE = "athlete"
    TRAINER = "trainer"
    ADMIN = "admin"


class User(Base, TimestampMixin):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True
    )
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.ATHLETE,
        nullable=False
    )
    language: Mapped[str] = mapped_column(
        String(5),
        default='ru',
        nullable=False
    )
    
    # Relationships
    workouts: Mapped[List["Workout"]] = relationship(
        "Workout",
        back_populates="trainer",
        foreign_keys="Workout.trainer_id"
    )
    bookings: Mapped[List["Booking"]] = relationship(
        "Booking",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, role={self.role.value})>"
    
    @property
    def full_name(self) -> str:
        """Полное имя пользователя"""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
    
    def is_admin(self) -> bool:
        """Проверка, является ли пользователь админом"""
        return self.role == UserRole.ADMIN
    
    def is_trainer(self) -> bool:
        """Проверка, является ли пользователь тренером (строго)"""
        return self.role == UserRole.TRAINER
    
    def has_trainer_permissions(self) -> bool:
        """Проверка, есть ли у пользователя права тренера (включая админа)"""
        return self.role in (UserRole.TRAINER, UserRole.ADMIN)
    
    def is_athlete(self) -> bool:
        """Проверка, является ли пользователь атлетом"""
        return self.role == UserRole.ATHLETE

