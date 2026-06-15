"""
Репозиторий для работы с привязкой тренеров по умолчанию
"""
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.workout_trainer import WorkoutTrainer


class WorkoutTrainerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> List[WorkoutTrainer]:
        result = await self.session.execute(
            select(WorkoutTrainer)
            .options(selectinload(WorkoutTrainer.trainer))
            .order_by(WorkoutTrainer.workout_name)
        )
        return list(result.scalars().all())

    async def get_by_workout_name(self, workout_name: str) -> Optional[WorkoutTrainer]:
        result = await self.session.execute(
            select(WorkoutTrainer)
            .where(WorkoutTrainer.workout_name == workout_name)
            .options(selectinload(WorkoutTrainer.trainer))
        )
        return result.scalar_one_or_none()

    async def set_trainer(self, workout_name: str, trainer_id: int) -> WorkoutTrainer:
        # Проверяем, существует ли привязка
        mapping = await self.get_by_workout_name(workout_name)
        if mapping:
            mapping.trainer_id = trainer_id
        else:
            mapping = WorkoutTrainer(workout_name=workout_name, trainer_id=trainer_id)
            self.session.add(mapping)
        await self.session.flush()
        return mapping

    async def delete(self, workout_name: str) -> bool:
        mapping = await self.get_by_workout_name(workout_name)
        if not mapping:
            return False
        await self.session.execute(
            delete(WorkoutTrainer).where(WorkoutTrainer.workout_name == workout_name)
        )
        return True
