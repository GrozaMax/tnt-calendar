"""
Репозиторий для работы с записями
"""
from datetime import date, datetime, time
from typing import Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import Booking, BookingStatus, Workout


class BookingRepository:
    """Репозиторий для работы с записями"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(
        self,
        booking_id: int,
        load_relations: bool = False
    ) -> Optional[Booking]:
        """Получить запись по ID"""
        if load_relations:
            result = await self.session.execute(
                select(Booking)
                .where(Booking.id == booking_id)
                .options(
                    selectinload(Booking.user),
                    selectinload(Booking.workout).selectinload(Workout.trainer)
                )
            )
            return result.scalar_one_or_none()
        return await self.session.get(Booking, booking_id)
    
    async def get_by_user_and_workout(
        self,
        user_id: int,
        workout_id: int
    ) -> Optional[Booking]:
        """Получить запись пользователя на конкретную тренировку"""
        result = await self.session.execute(
            select(Booking).where(
                and_(
                    Booking.user_id == user_id,
                    Booking.workout_id == workout_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_workout_booking(
        self,
        user_id: int,
        workout_id: int,
        status: Optional[BookingStatus] = None
    ) -> Optional[Booking]:
        """Получить запись пользователя на конкретную тренировку с фильтром по статусу"""
        conditions = [
            Booking.user_id == user_id,
            Booking.workout_id == workout_id
        ]
        
        if status:
            conditions.append(Booking.status == status)
        
        result = await self.session.execute(
            select(Booking).where(and_(*conditions))
        )
        return result.scalar_one_or_none()
    
    async def get_user_bookings(
        self,
        user_id: int,
        status: Optional[BookingStatus] = None,
        load_relations: bool = True
    ) -> list[Booking]:
        """Получить все записи пользователя"""
        conditions = [Booking.user_id == user_id]
        
        if status:
            conditions.append(Booking.status == status)
        
        query = select(Booking).where(and_(*conditions)).order_by(Booking.created_at.desc())
        
        if load_relations:
            query = query.options(
                selectinload(Booking.workout).selectinload(Workout.trainer)
            )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_active_bookings_by_date(
        self,
        user_id: int,
        target_date: date
    ) -> list[Booking]:
        """Получить активные записи пользователя на указанную дату"""
        start_datetime = datetime.combine(target_date, time.min)
        end_datetime = datetime.combine(target_date, time.max)
        
        result = await self.session.execute(
            select(Booking)
            .join(Workout)
            .where(
                and_(
                    Booking.user_id == user_id,
                    Booking.status == BookingStatus.ACTIVE,
                    Workout.datetime >= start_datetime,
                    Workout.datetime <= end_datetime
                )
            )
            .options(selectinload(Booking.workout))
        )
        return list(result.scalars().all())
    
    async def count_active_bookings_by_date(
        self,
        user_id: int,
        target_date: date
    ) -> int:
        """Подсчитать количество активных записей на указанную дату"""
        bookings = await self.get_active_bookings_by_date(user_id, target_date)
        return len(bookings)
    
    async def get_workout_bookings(
        self,
        workout_id: int,
        status: Optional[BookingStatus] = BookingStatus.ACTIVE,
        load_relations: bool = True
    ) -> list[Booking]:
        """Получить все записи на тренировку"""
        conditions = [Booking.workout_id == workout_id]
        
        if status:
            conditions.append(Booking.status == status)
        
        query = select(Booking).where(and_(*conditions)).order_by(Booking.created_at)
        
        if load_relations:
            query = query.options(selectinload(Booking.user))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create(
        self,
        user_id: int,
        workout_id: int,
        status: BookingStatus = BookingStatus.ACTIVE
    ) -> Booking:
        """Создать новую запись"""
        booking = Booking(
            user_id=user_id,
            workout_id=workout_id,
            status=status
        )
        self.session.add(booking)
        await self.session.flush()
        return booking
    
    async def cancel(self, booking_id: int) -> Optional[Booking]:
        """Отменить запись"""
        booking = await self.get_by_id(booking_id)
        if booking:
            booking.cancel()
            await self.session.flush()
        return booking
    
    async def delete(self, booking_id: int) -> bool:
        """Удалить запись"""
        booking = await self.get_by_id(booking_id)
        if not booking:
            return False
        
        await self.session.delete(booking)
        await self.session.flush()
        return True

