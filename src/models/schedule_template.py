"""
Модель шаблона недельного расписания
"""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class ScheduleTemplate(Base, TimestampMixin):
    """Слот шаблона недельного расписания"""
    __tablename__ = "schedule_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Пн, 6=Вс
    time: Mapped[str] = mapped_column(String(5), nullable=False)       # "HH:MM"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, default=60)
    max_participants: Mapped[int] = mapped_column(Integer, default=12)
