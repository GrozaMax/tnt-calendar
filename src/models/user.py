"""
Модель пользователя
"""
from __future__ import annotations

import enum
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Enum, BigInteger, Boolean
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
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
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
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    web_password_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )
    reminder_minutes: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
    )

    # ── Password helpers (hashlib, no external deps) ──────────────
    @staticmethod
    def _hash_password(plain: str, salt: str) -> str:
        import hashlib
        return hashlib.sha256(f"{salt}:{plain}".encode()).hexdigest()

    def set_web_password(self, plain: str) -> None:
        """Установить индивидуальный пароль для веб-панели."""
        import secrets
        salt = secrets.token_hex(16)
        h = self._hash_password(plain, salt)
        self.web_password_hash = f"{salt}${h}"

    def check_web_password(self, plain: str) -> bool:
        """Проверить пароль. Возвращает False если пароль не задан."""
        if not self.web_password_hash or "$" not in self.web_password_hash:
            return False
        salt, stored_hash = self.web_password_hash.split("$", 1)
        return self._hash_password(plain, salt) == stored_hash

    @property
    def has_web_password(self) -> bool:
        return bool(self.web_password_hash)

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
        from src.config import Config
        return self.role == UserRole.ADMIN or self.telegram_id in Config.ADMIN_TELEGRAM_IDS
    
    def is_trainer(self) -> bool:
        """Проверка, является ли пользователь тренером (строго)"""
        return self.role == UserRole.TRAINER
    
    def has_trainer_permissions(self) -> bool:
        """Проверка, есть ли у пользователя права тренера (включая админа)"""
        return self.is_admin() or self.role == UserRole.TRAINER

    def ui_role_key(self) -> str:
        """Роль для веба и клавиатур бота: супер-админ из ADMIN_TELEGRAM_IDS — 'admin'."""
        if self.is_admin():
            return UserRole.ADMIN.value
        if self.role == UserRole.TRAINER:
            return UserRole.TRAINER.value
        return UserRole.ATHLETE.value
    
    def is_athlete(self) -> bool:
        """Проверка, является ли пользователь атлетом"""
        return self.role == UserRole.ATHLETE

