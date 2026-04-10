"""
API для управления шаблоном недельного расписания
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from web.api.auth import get_current_user
from src.database import get_session
from src.database.repositories import ScheduleTemplateRepository
from src.models import User, UserRole

router = APIRouter()

DAY_NAMES = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]


class TemplateSlotCreate(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)
    time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    name: str = Field(..., min_length=1, max_length=255)
    duration: int = Field(default=60, gt=0, le=300)
    max_participants: int = Field(default=12, gt=0, le=200)


class TemplateSlotUpdate(BaseModel):
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    duration: Optional[int] = Field(None, gt=0, le=300)
    max_participants: Optional[int] = Field(None, gt=0, le=200)


class TemplateSlotResponse(BaseModel):
    id: int
    day_of_week: int
    day_name: str
    time: str
    name: str
    duration: int
    max_participants: int


def _to_response(slot) -> TemplateSlotResponse:
    return TemplateSlotResponse(
        id=slot.id,
        day_of_week=slot.day_of_week,
        day_name=DAY_NAMES[slot.day_of_week],
        time=slot.time,
        name=slot.name,
        duration=slot.duration,
        max_participants=slot.max_participants,
    )


def _require_admin(user: User):
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can manage schedule template")


@router.get("/", response_model=List[TemplateSlotResponse])
async def get_template(user: User = Depends(get_current_user)):
    """Получить все слоты шаблона"""
    async with get_session() as session:
        repo = ScheduleTemplateRepository(session)
        slots = await repo.get_all()
        return [_to_response(s) for s in slots]


@router.post("/", response_model=TemplateSlotResponse, status_code=status.HTTP_201_CREATED)
async def create_slot(data: TemplateSlotCreate, user: User = Depends(get_current_user)):
    """Добавить слот в шаблон"""
    _require_admin(user)
    async with get_session() as session:
        repo = ScheduleTemplateRepository(session)
        slot = await repo.create(
            day_of_week=data.day_of_week,
            time=data.time,
            name=data.name,
            duration=data.duration,
            max_participants=data.max_participants,
        )
        await session.commit()
        await session.refresh(slot)
        return _to_response(slot)


@router.put("/{slot_id}", response_model=TemplateSlotResponse)
async def update_slot(slot_id: int, data: TemplateSlotUpdate, user: User = Depends(get_current_user)):
    """Обновить слот шаблона"""
    _require_admin(user)
    async with get_session() as session:
        repo = ScheduleTemplateRepository(session)
        slot = await repo.update(slot_id, **data.model_dump(exclude_unset=True))
        if not slot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
        await session.commit()
        await session.refresh(slot)
        return _to_response(slot)


@router.delete("/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_slot(slot_id: int, user: User = Depends(get_current_user)):
    """Удалить слот шаблона"""
    _require_admin(user)
    async with get_session() as session:
        repo = ScheduleTemplateRepository(session)
        deleted = await repo.delete(slot_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
        await session.commit()


@router.post("/seed-from-file", status_code=status.HTTP_200_OK)
async def seed_from_file(force: bool = False, user: User = Depends(get_current_user)):
    """
    Перенести шаблон из create_weekly_schedule.py в базу данных.
    force=true — очищает существующий шаблон перед загрузкой.
    """
    _require_admin(user)
    from create_weekly_schedule import WEEKLY_SCHEDULE
    async with get_session() as session:
        repo = ScheduleTemplateRepository(session)
        count = await repo.count()
        if count > 0 and not force:
            return {"status": "skipped", "message": f"Шаблон уже содержит {count} слотов. Используйте force=true для перезаписи."}
        if force:
            await repo.delete_all()
        total = 0
        for day_of_week, slots in WEEKLY_SCHEDULE.items():
            for slot in slots:
                await repo.create(
                    day_of_week=day_of_week,
                    time=slot["time"],
                    name=slot["name"],
                    duration=slot["duration"],
                    max_participants=slot["max_participants"],
                )
                total += 1
        await session.commit()
    return {"status": "success", "created": total}
