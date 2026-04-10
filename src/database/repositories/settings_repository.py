"""
Настройки приложения в БД (лимиты и т.д.).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.constants import (
    DEFAULT_MAX_BOOKINGS_PER_DAY,
    MAX_MAX_BOOKINGS_PER_DAY,
    MIN_MAX_BOOKINGS_PER_DAY,
    SETTING_KEY_MAX_BOOKINGS_PER_DAY,
)
from src.models import AppSetting


class SettingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_value(self, key: str) -> str | None:
        result = await self.session.execute(
            select(AppSetting.value).where(AppSetting.key == key)
        )
        return result.scalar_one_or_none()

    async def set_value(self, key: str, value: str) -> None:
        row = await self.session.get(AppSetting, key)
        if row:
            row.value = value
        else:
            self.session.add(AppSetting(key=key, value=value))
        await self.session.flush()

    async def ensure_default_max_bookings_per_day(self) -> None:
        existing = await self.get_value(SETTING_KEY_MAX_BOOKINGS_PER_DAY)
        if existing is None:
            await self.set_value(
                SETTING_KEY_MAX_BOOKINGS_PER_DAY,
                str(DEFAULT_MAX_BOOKINGS_PER_DAY),
            )

    async def get_max_bookings_per_day(self) -> int:
        raw = await self.get_value(SETTING_KEY_MAX_BOOKINGS_PER_DAY)
        if raw is None:
            return DEFAULT_MAX_BOOKINGS_PER_DAY
        try:
            n = int(raw)
        except ValueError:
            return DEFAULT_MAX_BOOKINGS_PER_DAY
        return max(MIN_MAX_BOOKINGS_PER_DAY, min(n, MAX_MAX_BOOKINGS_PER_DAY))

    async def set_max_bookings_per_day(self, n: int) -> int:
        clamped = max(MIN_MAX_BOOKINGS_PER_DAY, min(int(n), MAX_MAX_BOOKINGS_PER_DAY))
        await self.set_value(SETTING_KEY_MAX_BOOKINGS_PER_DAY, str(clamped))
        return clamped
