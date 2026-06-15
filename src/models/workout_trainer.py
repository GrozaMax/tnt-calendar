"""
Модель для привязки тренера по умолчанию к типу тренировки
"""
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.user import User


class WorkoutTrainer(Base, TimestampMixin):
    """Связь названия тренировки и главного тренера по умолчанию"""
    __tablename__ = "workout_trainers"

    workout_name: Mapped[str] = mapped_column(String(255), primary_key=True)
    trainer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Relationships
    trainer: Mapped["User"] = relationship("User", foreign_keys=[trainer_id])
