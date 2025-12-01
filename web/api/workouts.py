"""
API для управления тренировками
"""
from datetime import datetime, date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from web.api.auth import get_current_user
from src.database import get_session
from src.database.repositories import WorkoutRepository, BookingRepository
from src.models import User, UserRole, BookingStatus, Workout, Booking

router = APIRouter()


class WorkoutCreate(BaseModel):
    """Создание тренировки"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    datetime: datetime
    duration: int = Field(default=60, gt=0, le=300)
    max_participants: int = Field(default=12, gt=0, le=100)
    trainer_id: Optional[int] = None


class WorkoutUpdate(BaseModel):
    """Обновление тренировки"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    datetime: Optional[datetime] = None
    duration: Optional[int] = Field(None, gt=0, le=300)
    max_participants: Optional[int] = Field(None, gt=0, le=100)
    trainer_id: Optional[int] = None


class WorkoutResponse(BaseModel):
    """Ответ с информацией о тренировке"""
    id: int
    name: str
    description: Optional[str]
    datetime: datetime
    duration: int
    max_participants: int
    current_participants: int
    trainer_id: int
    trainer_name: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BulkCreateRequest(BaseModel):
    """Массовое создание расписания"""
    weeks: int = Field(..., ge=1, le=12)
    trainer_id: Optional[int] = None


@router.get("/", response_model=List[WorkoutResponse])
async def get_workouts(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    trainer_id: Optional[int] = Query(None),
    user: User = Depends(get_current_user)
):
    """
    Получить список тренировок
    
    Параметры:
    - date_from: начальная дата (по умолчанию - сегодня)
    - date_to: конечная дата (по умолчанию - через неделю)
    - trainer_id: фильтр по тренеру
    """
    if not date_from:
        date_from = date.today()
    if not date_to:
        date_to = date_from + timedelta(days=7)
    
    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        
        # Если пользователь - тренер, показываем только его тренировки
        if user.role == UserRole.TRAINER and not trainer_id:
            trainer_id = user.id
        
        workouts = await workout_repo.get_by_date_range(
            date_from, 
            date_to
        )
        
        # Фильтруем по тренеру если нужно
        if trainer_id:
            workouts = [w for w in workouts if w.trainer_id == trainer_id]
        
        return [
            WorkoutResponse(
                id=w.id,
                name=w.name,
                description=w.description,
                datetime=w.datetime,
                duration=w.duration,
                max_participants=w.max_participants,
                current_participants=w.current_participants,
                trainer_id=w.trainer_id,
                trainer_name=w.trainer.full_name if w.trainer else "Unknown",
                created_at=w.created_at,
                updated_at=w.updated_at
            )
            for w in workouts
        ]


@router.get("/{workout_id}", response_model=WorkoutResponse)
async def get_workout(
    workout_id: int,
    user: User = Depends(get_current_user)
):
    """Получить информацию о конкретной тренировке"""
    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        workout = await workout_repo.get_by_id(workout_id, load_relations=True)
        
        if not workout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout not found"
            )
        
        # Тренер может видеть только свои тренировки
        if user.role == UserRole.TRAINER and workout.trainer_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own workouts"
            )
        
        return WorkoutResponse(
            id=workout.id,
            name=workout.name,
            description=workout.description,
            datetime=workout.datetime,
            duration=workout.duration,
            max_participants=workout.max_participants,
            current_participants=workout.current_participants,
            trainer_id=workout.trainer_id,
            trainer_name=workout.trainer.full_name if workout.trainer else "Unknown",
            created_at=workout.created_at,
            updated_at=workout.updated_at
        )


@router.post("/", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
async def create_workout(
    workout_data: WorkoutCreate,
    user: User = Depends(get_current_user)
):
    """Создать новую тренировку"""
    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        
        # Если trainer_id не указан, используем текущего пользователя
        trainer_id = workout_data.trainer_id
        if not trainer_id:
            trainer_id = user.id
        
        # Тренер может создавать только для себя
        if user.role == UserRole.TRAINER and trainer_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Trainers can only create workouts for themselves"
            )
        
        # Создаём тренировку
        workout = await workout_repo.create(
            name=workout_data.name,
            description=workout_data.description,
            datetime=workout_data.datetime,
            duration=workout_data.duration,
            max_participants=workout_data.max_participants,
            trainer_id=trainer_id
        )
        
        await session.commit()
        await session.refresh(workout)
        
        # Загружаем связи
        workout = await workout_repo.get_by_id(workout.id, load_relations=True)
        
        return WorkoutResponse(
            id=workout.id,
            name=workout.name,
            description=workout.description,
            datetime=workout.datetime,
            duration=workout.duration,
            max_participants=workout.max_participants,
            current_participants=workout.current_participants,
            trainer_id=workout.trainer_id,
            trainer_name=workout.trainer.full_name if workout.trainer else "Unknown",
            created_at=workout.created_at,
            updated_at=workout.updated_at
        )


@router.put("/{workout_id}", response_model=WorkoutResponse)
async def update_workout(
    workout_id: int,
    workout_data: WorkoutUpdate,
    user: User = Depends(get_current_user)
):
    """Обновить тренировку"""
    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        workout = await workout_repo.get_by_id(workout_id)
        
        if not workout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout not found"
            )
        
        # Тренер может редактировать только свои тренировки
        if user.role == UserRole.TRAINER and workout.trainer_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own workouts"
            )
        
        # Обновляем данные
        update_data = workout_data.model_dump(exclude_unset=True)
        
        # Тренер не может менять trainer_id
        if user.role == UserRole.TRAINER and 'trainer_id' in update_data:
            del update_data['trainer_id']
        
        workout = await workout_repo.update(workout_id, **update_data)
        await session.commit()
        
        # Загружаем обновлённые данные со связями
        workout = await workout_repo.get_by_id(workout_id, load_relations=True)
        
        return WorkoutResponse(
            id=workout.id,
            name=workout.name,
            description=workout.description,
            datetime=workout.datetime,
            duration=workout.duration,
            max_participants=workout.max_participants,
            current_participants=workout.current_participants,
            trainer_id=workout.trainer_id,
            trainer_name=workout.trainer.full_name if workout.trainer else "Unknown",
            created_at=workout.created_at,
            updated_at=workout.updated_at
        )


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workout(
    workout_id: int,
    user: User = Depends(get_current_user)
):
    """Удалить тренировку"""
    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        workout = await workout_repo.get_by_id(workout_id)
        
        if not workout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout not found"
            )
        
        # Тренер может удалять только свои тренировки
        if user.role == UserRole.TRAINER and workout.trainer_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own workouts"
            )
        
        success = await workout_repo.delete(workout_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete workout"
            )
        
        await session.commit()


@router.get("/{workout_id}/participants")
async def get_workout_participants(
    workout_id: int,
    user: User = Depends(get_current_user)
):
    """Получить список участников тренировки"""
    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        booking_repo = BookingRepository(session)
        
        workout = await workout_repo.get_by_id(workout_id, load_relations=True)
        
        if not workout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout not found"
            )
        
        # Тренер может видеть только участников своих тренировок
        if user.role == UserRole.TRAINER and workout.trainer_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view participants of your own workouts"
            )
        
        bookings = await booking_repo.get_workout_bookings(
            workout_id,
            status=BookingStatus.ACTIVE,
            load_relations=True
        )
        
        return {
            "workout_id": workout_id,
            "workout_name": workout.name,
            "workout_datetime": workout.datetime,
            "total_participants": len(bookings),
            "max_participants": workout.max_participants,
            "participants": [
                {
                    "booking_id": b.id,
                    "user_id": b.user_id,
                    "full_name": b.user.full_name,
                    "username": b.user.username,
                    "created_at": b.created_at
                }
                for b in bookings
            ]
        }


@router.post("/clear-all", status_code=status.HTTP_200_OK)
async def clear_all_workouts(
    user: User = Depends(get_current_user)
):
    """
    Удалить ВСЕ тренировки из базы данных
    
    ВНИМАНИЕ: Это действие необратимо!
    Только для админов.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Clear all workouts called by user {user.id} (role: {user.role.value})")
    
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can clear all workouts"
        )
    
    from sqlalchemy import delete as sql_delete, func, select as sql_select
    
    async with get_session() as session:
        # Подсчитываем количество тренировок и записей
        total_workouts = await session.execute(
            sql_select(func.count(Workout.id))
        )
        workouts_count = total_workouts.scalar()
        
        total_bookings = await session.execute(
            sql_select(func.count(Booking.id))
        )
        bookings_count = total_bookings.scalar()
        
        # Удаляем все записи
        await session.execute(sql_delete(Booking))
        
        # Удаляем все тренировки
        await session.execute(sql_delete(Workout))
        
        await session.commit()
    
    return {
        "status": "success",
        "deleted_workouts": workouts_count,
        "deleted_bookings": bookings_count,
        "message": f"Удалено {workouts_count} тренировок и {bookings_count} записей"
    }


@router.post("/bulk-create")
async def bulk_create_schedule(
    request: BulkCreateRequest,
    user: User = Depends(get_current_user)
):
    """
    Массовое создание расписания на N недель
    
    Использует шаблон из create_weekly_schedule.py
    Только для админов.
    """
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can bulk create schedules"
        )
    
    # Импортируем шаблон расписания
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from create_weekly_schedule import WEEKLY_SCHEDULE
    
    async with get_session() as session:
        workout_repo = WorkoutRepository(session)
        
        # Определяем тренера
        trainer_id = request.trainer_id if request.trainer_id else user.id
        
        # ВАЖНО: Начинаем с понедельника текущей недели
        import logging
        logger = logging.getLogger(__name__)
        
        today = datetime.now().date()
        # Вычисляем сдвиг до понедельника (0 = понедельник)
        days_since_monday = today.weekday()  # 0=Пн, 1=Вт, 2=Ср, ..., 6=Вс
        start_date = today - timedelta(days=days_since_monday)
        
        logger.info(f"📅 Создание расписания:")
        logger.info(f"  Сегодня: {today} ({['Пн','Вт','Ср','Чт','Пт','Сб','Вс'][today.weekday()]})")
        logger.info(f"  Дней с понедельника: {days_since_monday}")
        logger.info(f"  Начало расписания: {start_date} ({['Пн','Вт','Ср','Чт','Пт','Сб','Вс'][start_date.weekday()]})")
        logger.info(f"  Недель для создания: {request.weeks}")
        
        total_created = 0
        total_skipped = 0
        
        # Создаём расписание
        created_by_date = {}  # Для отладки
        
        for week in range(request.weeks):
            for days_offset in range(7):
                current_date = start_date + timedelta(days=week * 7 + days_offset)
                weekday = current_date.weekday()
                
                day_schedule = WEEKLY_SCHEDULE.get(weekday, [])
                
                for slot in day_schedule:
                    hour, minute = map(int, slot["time"].split(":"))
                    workout_datetime = datetime.combine(current_date, datetime.min.time())
                    workout_datetime = workout_datetime.replace(hour=hour, minute=minute)
                    
                    # Проверяем существование
                    existing = await workout_repo.get_by_date(current_date)
                    exists = any(
                        w.datetime == workout_datetime and w.name == slot["name"]
                        for w in existing
                    )
                    
                    if exists:
                        total_skipped += 1
                        continue
                    
                    # Создаём
                    await workout_repo.create(
                        name=slot["name"],
                        datetime=workout_datetime,
                        trainer_id=trainer_id,
                        duration=slot["duration"],
                        max_participants=slot["max_participants"]
                    )
                    logger.debug(f"  ✅ Создана: {workout_datetime.strftime('%d.%m (%a) %H:%M')} - {slot['name']}")
                    total_created += 1
                    
                    # Для отладки
                    date_key = current_date.isoformat()
                    if date_key not in created_by_date:
                        created_by_date[date_key] = 0
                    created_by_date[date_key] += 1
        
        await session.commit()
        
        logger.info(f"✅ Создание завершено:")
        logger.info(f"  Создано: {total_created}")
        logger.info(f"  Пропущено: {total_skipped}")
    
    return {
        "status": "success",
        "weeks": request.weeks,
        "created": total_created,
        "skipped": total_skipped,
        "total": total_created + total_skipped,
        "start_date": start_date.isoformat(),
        "today": today.isoformat(),
        "created_by_date": created_by_date,
        "debug": {
            "today": today.isoformat(),
            "today_weekday": today.weekday(),
            "start_date": start_date.isoformat(),
            "start_weekday": start_date.weekday()
        }
    }

