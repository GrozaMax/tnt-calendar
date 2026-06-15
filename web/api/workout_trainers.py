"""
API для управления тренерами по умолчанию для типов занятий
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from web.api.auth import get_current_user
from src.database import get_session
from src.database.repositories import (
    WorkoutTrainerRepository,
    ScheduleTemplateRepository,
    UserRepository,
)
from src.models import User, UserRole

router = APIRouter()


class WorkoutTrainerSet(BaseModel):
    workout_name: str = Field(..., min_length=1, max_length=255)
    trainer_id: Optional[int] = None


def _require_admin(user: User):
    if not user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can manage default trainers",
        )


@router.get("")
async def get_workout_trainers(user: User = Depends(get_current_user)):
    """Получить список типов тренировок и их тренеров по умолчанию"""
    _require_admin(user)
    async with get_session() as session:
        wt_repo = WorkoutTrainerRepository(session)
        mappings_list = await wt_repo.get_all()
        
        # Получаем все уникальные названия тренировок из шаблона
        template_repo = ScheduleTemplateRepository(session)
        slots = await template_repo.get_all()
        template_names = {s.name for s in slots}
        
        # Стандартные названия (дефолтные)
        default_names = {
            "CrossFit",
            "Weightlifting",
            "Yoga",
            "Stratching",
            "Thai Boxing",
            "CrossFit Beginners",
            "CrossFit Football",
        }
        
        # Объединяем и сортируем
        all_workout_names = sorted(list(template_names | default_names))
        
        # Формируем словарь текущих маппингов
        mappings = {m.workout_name: m.trainer_id for m in mappings_list}
        
        return {
            "workout_names": all_workout_names,
            "mappings": mappings
        }


@router.post("")
async def set_workout_trainer(body: WorkoutTrainerSet, user: User = Depends(get_current_user)):
    """Установить или удалить тренера по умолчанию для типа тренировки"""
    _require_admin(user)
    async with get_session() as session:
        wt_repo = WorkoutTrainerRepository(session)
        if body.trainer_id is None:
            deleted = await wt_repo.delete(body.workout_name)
            await session.commit()
            return {"status": "deleted" if deleted else "not_found"}
        else:
            # Проверяем, что тренер существует и имеет роль TRAINER или ADMIN
            user_repo = UserRepository(session)
            trainer_user = await user_repo.get_by_id(body.trainer_id)
            if not trainer_user or trainer_user.role not in [UserRole.TRAINER, UserRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is not a valid trainer or administrator",
                )
            mapping = await wt_repo.set_trainer(body.workout_name, body.trainer_id)
            await session.commit()
            return {
                "status": "success",
                "workout_name": mapping.workout_name,
                "trainer_id": mapping.trainer_id
            }
