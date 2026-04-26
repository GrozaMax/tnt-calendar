"""
API для аналитики
"""
from typing import Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.database.connection import get_session
from src.models import Workout, User
from web.api.auth import require_admin

router = APIRouter()

@router.get("/heatmap")
async def get_heatmap_data(
    days_back: int = 30,
    admin: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Возвращает данные для тепловой карты: заполняемость по дням недели и времени"""
    
    start_date = datetime.now() - timedelta(days=days_back)
    
    query = (
        select(Workout)
        .options(joinedload(Workout.bookings))
        .where(Workout.datetime >= start_date)
    )
    async with get_session() as session:
        result = await session.execute(query)
        workouts = result.unique().scalars().all()
    
    # Агрегация данных
    # Ключ: "день_недели-время" (например, "0-18:00", где 0 - понедельник)
    # Значение: {"total_participants": 0, "total_max": 0, "count": 0}
    
    heatmap_data = {}
    
    for w in workouts:
        # 0 = Понедельник, 6 = Воскресенье
        weekday = w.datetime.weekday()
        time_str = w.datetime.strftime("%H:%M")
        
        key = f"{weekday}-{time_str}"
        
        if key not in heatmap_data:
            heatmap_data[key] = {
                "total_participants": 0,
                "total_max": 0,
                "count": 0,
                "weekday": weekday,
                "time": time_str
            }
            
        heatmap_data[key]["total_participants"] += w.current_participants
        heatmap_data[key]["total_max"] += w.max_participants
        heatmap_data[key]["count"] += 1
        
    # Форматируем результат для фронтенда
    formatted_data = []
    for key, stats in heatmap_data.items():
        avg_fill_rate = 0
        if stats["total_max"] > 0:
            avg_fill_rate = stats["total_participants"] / stats["total_max"]
            
        formatted_data.append({
            "weekday": stats["weekday"],
            "time": stats["time"],
            "avg_participants": stats["total_participants"] / stats["count"],
            "avg_max": stats["total_max"] / stats["count"],
            "fill_rate": avg_fill_rate,
            "count": stats["count"]
        })
        
    return {
        "start_date": start_date.isoformat(),
        "end_date": datetime.now().isoformat(),
        "total_workouts": len(workouts),
        "heatmap": formatted_data
    }
