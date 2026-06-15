"""
ORM модели для базы данных
"""
from src.models.base import Base
from src.models.user import User, UserRole
from src.models.workout import Workout
from src.models.booking import Booking, BookingStatus
from src.models.schedule_template import ScheduleTemplate
from src.models.app_setting import AppSetting
from src.models.workout_trainer import WorkoutTrainer

__all__ = [
    'Base',
    'User',
    'UserRole',
    'Workout',
    'Booking',
    'BookingStatus',
    'ScheduleTemplate',
    'AppSetting',
    'WorkoutTrainer',
]

