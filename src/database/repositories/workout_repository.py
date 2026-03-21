"""
Репозиторий для работы с тренировками
"""
from datetime import datetime, date, time, timedelta
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import Workout


class WorkoutRepository:
    """Репозиторий для работы с тренировками"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(
        self,
        workout_id: int,
        load_relations: bool = False
    ) -> Optional[Workout]:
        """
        Получить тренировку по ID.
        
        Args:
            workout_id: ID тренировки
            load_relations: Загружать ли связанные объекты (trainer, bookings)
        """
        if load_relations:
            result = await self.session.execute(
                select(Workout)
                .where(Workout.id == workout_id)
                .options(
                    selectinload(Workout.trainer),
                    selectinload(Workout.bookings)
                )
            )
            return result.scalar_one_or_none()
        return await self.session.get(Workout, workout_id)
    
    async def get_by_date(
        self,
        target_date: date,
        load_relations: bool = True
    ) -> list[Workout]:
        """
        Получить все тренировки на указанную дату.
        
        Args:
            target_date: Дата
            load_relations: Загружать ли связанные объекты
        """
        start_datetime = datetime.combine(target_date, time.min)
        end_datetime = datetime.combine(target_date, time.max)
        
        query = (
            select(Workout)
            .where(
                and_(
                    Workout.datetime >= start_datetime,
                    Workout.datetime <= end_datetime
                )
            )
            .order_by(Workout.datetime)
        )
        
        if load_relations:
            query = query.options(
                selectinload(Workout.trainer),
                selectinload(Workout.bookings)
            )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_date_range(
        self,
        start_date: date,
        end_date: date,
        trainer_id: Optional[int] = None
    ) -> list[Workout]:
        """
        Получить тренировки в диапазоне дат.
        
        Args:
            start_date: Начальная дата
            end_date: Конечная дата
            trainer_id: ID тренера (опционально)
        """
        start_datetime = datetime.combine(start_date, time.min)
        end_datetime = datetime.combine(end_date, time.max)
        
        conditions = [
            Workout.datetime >= start_datetime,
            Workout.datetime <= end_datetime
        ]
        
        if trainer_id:
            conditions.append(Workout.trainer_id == trainer_id)
        
        result = await self.session.execute(
            select(Workout)
            .where(and_(*conditions))
            .order_by(Workout.datetime)
            .options(
                selectinload(Workout.trainer),
                selectinload(Workout.bookings)
            )
        )
        return list(result.scalars().all())
    
    async def create(
        self,
        name: str,
        datetime: datetime,
        trainer_id: int,
        description: Optional[str] = None,
        duration: int = 60,
        max_participants: int = 999
    ) -> Workout:
        """Создать новую тренировку"""
        workout = Workout(
            name=name,
            description=description,
            datetime=datetime,
            duration=duration,
            max_participants=max_participants,
            trainer_id=trainer_id
        )
        self.session.add(workout)
        await self.session.flush()
        return workout
    
    async def update(
        self,
        workout_id: int,
        **kwargs
    ) -> Optional[Workout]:
        """Обновить тренировку"""
        workout = await self.get_by_id(workout_id)
        if not workout:
            return None
        
        for key, value in kwargs.items():
            if hasattr(workout, key):
                setattr(workout, key, value)
        
        await self.session.flush()
        return workout
    
    async def delete(self, workout_id: int) -> bool:
        """
        Удалить тренировку.
        ВАЖНО: Требует session.commit() после вызова!
        """
        from sqlalchemy import delete as sql_delete
        from src.models import Booking
        
        # Загружаем со связями
        workout = await self.get_by_id(workout_id, load_relations=True)
        if not workout:
            return False
        
        # ВАЖНО: Сначала явно удаляем все связанные записи (bookings)
        # Это необходимо, так как PRAGMA foreign_keys может быть выключен
        delete_bookings_stmt = sql_delete(Booking).where(Booking.workout_id == workout_id)
        result = await self.session.execute(delete_bookings_stmt)
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Удалено записей (bookings) для тренировки {workout_id}: {result.rowcount}")
        
        # Теперь удаляем саму тренировку
        delete_workout_stmt = sql_delete(Workout).where(Workout.id == workout_id)
        result = await self.session.execute(delete_workout_stmt)
        logger.info(f"Удалено тренировок: {result.rowcount}")
        
        # Применяем изменения в сессии
        await self.session.flush()
        
        return True
    
    async def get_unassigned_workouts(self, days: int = 7) -> list[Workout]:
        """Получить тренировки без назначенного тренера на ближайшие N дней"""
        now = datetime.utcnow()
        end = now + timedelta(days=days)
        result = await self.session.execute(
            select(Workout)
            .where(
                Workout.trainer_id.is_(None),
                Workout.datetime >= now,
                Workout.datetime <= end
            )
            .order_by(Workout.datetime)
            .options(selectinload(Workout.bookings))
        )
        return list(result.scalars().all())

    async def assign_trainer(self, workout_id: int, trainer_id: int) -> Optional[Workout]:
        """Назначить тренера на тренировку"""
        workout = await self.get_by_id(workout_id)
        if not workout:
            return None
        workout.trainer_id = trainer_id
        await self.session.flush()
        return workout

    async def get_upcoming_workouts(
        self,
        limit: int = 10,
        trainer_id: Optional[int] = None
    ) -> list[Workout]:
        """Получить предстоящие тренировки"""
        now = datetime.utcnow()
        
        conditions = [Workout.datetime > now]
        if trainer_id:
            conditions.append(Workout.trainer_id == trainer_id)
        
        result = await self.session.execute(
            select(Workout)
            .where(and_(*conditions))
            .order_by(Workout.datetime)
            .limit(limit)
            .options(
                selectinload(Workout.trainer),
                selectinload(Workout.bookings)
            )
        )
        return list(result.scalars().all())

