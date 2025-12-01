"""
Скрипт для создания базового недельного расписания
"""
import asyncio
from datetime import datetime, timedelta

from src.database import get_session, init_db
from src.database.repositories import UserRepository, WorkoutRepository


# Полное расписание на неделю
WEEKLY_SCHEDULE = {
    0: [  # Понедельник
        {"time": "08:00", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "09:30", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "12:30", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "17:00", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "18:30", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "20:00", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "21:30", "name": "Yoga", "duration": 60, "max_participants": 15},
    ],
    1: [  # Вторник
        {"time": "08:00", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "09:30", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "12:30", "name": "Weightlifting", "duration": 60, "max_participants": 10},
        {"time": "14:00", "name": "CrossFit Football", "duration": 60, "max_participants": 12},
        {"time": "15:00", "name": "Thai Boxing", "duration": 60, "max_participants": 15},
        {"time": "18:00", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "19:30", "name": "Weightlifting", "duration": 60, "max_participants": 10},
        {"time": "20:30", "name": "CrossFit", "duration": 90, "max_participants": 12},
    ],
    2: [  # Среда
        {"time": "08:00", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "09:30", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "11:00", "name": "Yoga", "duration": 60, "max_participants": 15},
        {"time": "12:30", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "17:00", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "20:00", "name": "CrossFit", "duration": 90, "max_participants": 12},
    ],
    3: [  # Четверг
        {"time": "08:00", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "09:30", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "12:30", "name": "Weightlifting", "duration": 60, "max_participants": 10},
        {"time": "14:00", "name": "CrossFit Football", "duration": 60, "max_participants": 12},
        {"time": "15:00", "name": "Thai Boxing", "duration": 60, "max_participants": 15},
        {"time": "18:00", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "19:30", "name": "Weightlifting", "duration": 60, "max_participants": 10},
        {"time": "20:30", "name": "CrossFit", "duration": 90, "max_participants": 12},
    ],
    4: [  # Пятница
        {"time": "08:00", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "09:30", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "12:30", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "17:00", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "18:30", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "21:30", "name": "Yoga", "duration": 60, "max_participants": 15},
    ],
    5: [  # Суббота
        {"time": "09:30", "name": "Yoga", "duration": 60, "max_participants": 15},
        {"time": "11:00", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "12:30", "name": "Weightlifting", "duration": 60, "max_participants": 10},
        {"time": "14:00", "name": "CrossFit Football", "duration": 60, "max_participants": 12},
        {"time": "15:00", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "16:00", "name": "Thai Boxing", "duration": 60, "max_participants": 15},
    ],
    6: [  # Воскресенье
        {"time": "12:30", "name": "CrossFit", "duration": 90, "max_participants": 12},
        {"time": "14:00", "name": "CrossFit", "duration": 90, "max_participants": 12},
    ],
}

WEEKDAY_NAMES = {
    0: "Понедельник",
    1: "Вторник",
    2: "Среда",
    3: "Четверг",
    4: "Пятница",
    5: "Суббота",
    6: "Воскресенье",
}


async def create_weekly_schedule(weeks_ahead: int = 4):
    """
    Создать расписание на несколько недель вперед
    
    Args:
        weeks_ahead: Количество недель для создания расписания
    """
    # Инициализация БД
    print("🔧 Инициализация базы данных...")
    await init_db()
    print("✅ База данных инициализирована\n")
    
    async with get_session() as session:
        user_repo = UserRepository(session)
        workout_repo = WorkoutRepository(session)
        
        # Получаем тренера
        trainers = await user_repo.get_all_trainers()
        if not trainers:
            print("❌ Не найдено ни одного тренера в системе!")
            print("💡 Создайте тренера через create_test_data.py")
            return
        
        trainer = trainers[0]
        print(f"👤 Используем тренера: {trainer.full_name} (ID: {trainer.telegram_id})\n")
        
        # Начинаем с сегодняшнего дня
        start_date = datetime.now().date()
        
        print(f"📅 Создаём расписание на {weeks_ahead} недель")
        print(f"📍 Начиная с: {start_date.strftime('%d.%m.%Y')}\n")
        print("=" * 60)
        
        total_created = 0
        total_skipped = 0
        
        # Создаём расписание на каждую неделю
        for week in range(weeks_ahead):
            print(f"\n📆 НЕДЕЛЯ {week + 1}")
            print("-" * 60)
            
            week_created = 0
            
            # Для каждого дня недели
            for days_offset in range(7):
                current_date = start_date + timedelta(days=week * 7 + days_offset)
                weekday = current_date.weekday()
                
                # Пропускаем прошедшие дни в первой неделе
                if current_date < datetime.now().date():
                    continue
                
                # Получаем расписание на этот день недели
                day_schedule = WEEKLY_SCHEDULE.get(weekday, [])
                
                if not day_schedule:
                    continue
                
                print(f"\n{WEEKDAY_NAMES[weekday]}, {current_date.strftime('%d.%m.%Y')}:")
                
                # Создаём тренировки на этот день
                for slot in day_schedule:
                    hour, minute = map(int, slot["time"].split(":"))
                    workout_datetime = datetime.combine(current_date, datetime.min.time())
                    workout_datetime = workout_datetime.replace(hour=hour, minute=minute)
                    
                    # Проверяем, не существует ли уже тренировка в это время
                    existing = await workout_repo.get_by_date(current_date)
                    exists = any(
                        w.datetime == workout_datetime and w.name == slot["name"]
                        for w in existing
                    )
                    
                    if exists:
                        print(f"  ⚠️  {slot['time']} - {slot['name']} - уже существует")
                        total_skipped += 1
                        continue
                    
                    # Создаём тренировку
                    await workout_repo.create(
                        name=slot["name"],
                        datetime=workout_datetime,
                        trainer_id=trainer.id,
                        duration=slot["duration"],
                        max_participants=slot["max_participants"]
                    )
                    print(f"  ✅ {slot['time']} - {slot['name']} ({slot['duration']} мин)")
                    week_created += 1
                    total_created += 1
            
            print(f"\n  📊 Создано на неделю: {week_created}")
            
            # Сохраняем изменения после каждой недели
            await session.commit()
        
        print("\n" + "=" * 60)
        print(f"\n🎉 ГОТОВО!")
        print(f"✅ Всего создано тренировок: {total_created}")
        print(f"⚠️  Пропущено (уже существуют): {total_skipped}")
        print(f"📅 Расписание создано на {weeks_ahead} недель вперёд")
        
        # Статистика по типам тренировок
        print(f"\n📊 Статистика (в неделю):")
        all_workouts = []
        for day_schedule in WEEKLY_SCHEDULE.values():
            all_workouts.extend(day_schedule)
        
        workout_types = {}
        for workout in all_workouts:
            name = workout["name"]
            workout_types[name] = workout_types.get(name, 0) + 1
        
        for name, count in sorted(workout_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {name}: {count} занятий")
        
        print(f"\n  📈 Итого занятий в неделю: {len(all_workouts)}")


if __name__ == '__main__':
    print("🚀 Создание базового недельного расписания CrossFit Hub\n")
    
    # Можно изменить количество недель
    WEEKS_AHEAD = 4  # Создать расписание на 4 недели вперед
    
    asyncio.run(create_weekly_schedule(weeks_ahead=WEEKS_AHEAD))

