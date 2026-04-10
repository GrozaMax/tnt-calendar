"""
Настройки зала (лимиты записей и т.д.) — только админ.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from web.api.auth import get_current_user
from src.database import get_session
from src.database.repositories.settings_repository import SettingsRepository
from src.constants import MAX_MAX_BOOKINGS_PER_DAY, MIN_MAX_BOOKINGS_PER_DAY
from src.models import User, UserRole

router = APIRouter()


class GymSettingsOut(BaseModel):
    max_bookings_per_day: int


class GymSettingsPatch(BaseModel):
    max_bookings_per_day: int = Field(
        ge=MIN_MAX_BOOKINGS_PER_DAY,
        le=MAX_MAX_BOOKINGS_PER_DAY,
    )


@router.get("", response_model=GymSettingsOut)
async def get_gym_settings(user: User = Depends(get_current_user)):
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view gym settings",
        )
    async with get_session() as session:
        repo = SettingsRepository(session)
        await repo.ensure_default_max_bookings_per_day()
        n = await repo.get_max_bookings_per_day()
        await session.commit()
    return GymSettingsOut(max_bookings_per_day=n)


@router.patch("", response_model=GymSettingsOut)
async def patch_gym_settings(
    body: GymSettingsPatch,
    user: User = Depends(get_current_user),
):
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can change gym settings",
        )
    async with get_session() as session:
        repo = SettingsRepository(session)
        n = await repo.set_max_bookings_per_day(body.max_bookings_per_day)
        await session.commit()
    return GymSettingsOut(max_bookings_per_day=n)
