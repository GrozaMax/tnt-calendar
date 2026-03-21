"""
Репозиторий для работы с шаблоном расписания
"""
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.schedule_template import ScheduleTemplate


class ScheduleTemplateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> List[ScheduleTemplate]:
        result = await self.session.execute(
            select(ScheduleTemplate).order_by(ScheduleTemplate.day_of_week, ScheduleTemplate.time)
        )
        return list(result.scalars().all())

    async def get_by_day(self, day_of_week: int) -> List[ScheduleTemplate]:
        result = await self.session.execute(
            select(ScheduleTemplate)
            .where(ScheduleTemplate.day_of_week == day_of_week)
            .order_by(ScheduleTemplate.time)
        )
        return list(result.scalars().all())

    async def get_by_id(self, template_id: int) -> Optional[ScheduleTemplate]:
        result = await self.session.execute(
            select(ScheduleTemplate).where(ScheduleTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def create(self, day_of_week: int, time: str, name: str,
                     duration: int = 60, max_participants: int = 12) -> ScheduleTemplate:
        slot = ScheduleTemplate(
            day_of_week=day_of_week,
            time=time,
            name=name,
            duration=duration,
            max_participants=max_participants,
        )
        self.session.add(slot)
        await self.session.flush()
        return slot

    async def update(self, template_id: int, **kwargs) -> Optional[ScheduleTemplate]:
        slot = await self.get_by_id(template_id)
        if not slot:
            return None
        for key, value in kwargs.items():
            if hasattr(slot, key):
                setattr(slot, key, value)
        await self.session.flush()
        return slot

    async def delete(self, template_id: int) -> bool:
        slot = await self.get_by_id(template_id)
        if not slot:
            return False
        await self.session.execute(delete(ScheduleTemplate).where(ScheduleTemplate.id == template_id))
        return True

    async def delete_all(self) -> None:
        await self.session.execute(delete(ScheduleTemplate))

    async def count(self) -> int:
        result = await self.session.execute(select(ScheduleTemplate))
        return len(result.scalars().all())
