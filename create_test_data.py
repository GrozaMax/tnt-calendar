"""
Скрипт для создания тестовых данных
"""
import asyncio
from datetime import datetime, timedelta

from src.database import get_session, init_db
from src.database.repositories import UserRepository, WorkoutRepository
from src.models import UserRole


async def create_test_data():
    """Создать тестовые тренировки и тренера"""
    # Инициализация БД (создание таблиц)
    print("🔧 Инициализация базы данных...")
    await init_db()
    print("✅ База данных инициализирована\n")
    
    async with get_session() as session:
        user_repo = UserRepository(session)
        workout_repo = WorkoutRepository(session)
        
        print("📝 Создание тестового тренера...")
        
        # Создать тренера (замените на свой Telegram ID)
        trainer, created = await user_repo.get_or_create(
            telegram_id=123456789,  # ЗАМЕНИТЕ НА СВОЙ TELEGRAM ID
            first_name="Тренер",
            last_name="Иванов",
            username="trainer_ivan"
        )
        
        if created:
            print(f"✅ Создан новый тренер: {trainer.full_name}")
        else:
            print(f"ℹ️ Тренер уже существует: {trainer.full_name}")
        
        # Назначить роль тренера
        if trainer.role != UserRole.TRAINER:
            trainer.role = UserRole.TRAINER
            print(f"✅ Роль тренера назначена")
        
        print("\n📋 Создание тестовых тренировок...")
        
        # Получить текущее время
        now = datetime.now()
        
        # Создать тренировки на сегодня
        today_morning = now.replace(hour=10, minute=0, second=0, microsecond=0)
        if today_morning > now:
            workout1 = await workout_repo.create(
                name="CrossFit Beginner",
                description="Тренировка для начинающих",
                datetime=today_morning,
                trainer_id=trainer.id,
                duration=60,
                max_participants=10
            )
            print(f"✅ Создана тренировка: {workout1.name} на {workout1.datetime}")
        
        today_evening = now.replace(hour=18, minute=30, second=0, microsecond=0)
        if today_evening > now:
            workout2 = await workout_repo.create(
                name="CrossFit WOD",
                description="Workout of the Day",
                datetime=today_evening,
                trainer_id=trainer.id,
                duration=60,
                max_participants=12
            )
            print(f"✅ Создана тренировка: {workout2.name} на {workout2.datetime}")
        
        # Создать тренировки на завтра
        tomorrow = now + timedelta(days=1)
        
        tomorrow_morning = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        workout3 = await workout_repo.create(
            name="Olympic Lifting",
            description="Тяжелая атлетика",
            datetime=tomorrow_morning,
            trainer_id=trainer.id,
            duration=90,
            max_participants=8
        )
        print(f"✅ Создана тренировка: {workout3.name} на {workout3.datetime}")
        
        tomorrow_afternoon = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        workout4 = await workout_repo.create(
            name="Functional Training",
            description="Функциональный тренинг",
            datetime=tomorrow_afternoon,
            trainer_id=trainer.id,
            duration=60,
            max_participants=15
        )
        print(f"✅ Создана тренировка: {workout4.name} на {workout4.datetime}")
        
        tomorrow_evening = tomorrow.replace(hour=19, minute=0, second=0, microsecond=0)
        workout5 = await workout_repo.create(
            name="CrossFit Advanced",
            description="Для продвинутых атлетов",
            datetime=tomorrow_evening,
            trainer_id=trainer.id,
            duration=75,
            max_participants=10
        )
        print(f"✅ Создана тренировка: {workout5.name} на {workout5.datetime}")
        
        # Сохранить изменения
        await session.commit()
        
        print("\n✅ Все тестовые данные созданы успешно!")
        print(f"\n📊 Создано тренировок: 5")
        print(f"👤 Тренер: {trainer.full_name} (ID: {trainer.telegram_id})")
        print(f"\n⚠️ Не забудьте заменить telegram_id тренера в файле на свой!")


if __name__ == '__main__':
    print("🚀 Запуск создания тестовых данных...\n")
    asyncio.run(create_test_data())

