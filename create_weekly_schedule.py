"""
Актуальное расписание CrossFit зала на неделю
Обновлено: 1 декабря 2025
"""

# Расписание по дням недели (0 = понедельник, 6 = воскресенье)
WEEKLY_SCHEDULE = {
    0: [  # ПОНЕДЕЛЬНИК
        {"time": "08:00", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "09:30", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "12:30", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "14:00", "name": "CrossFit Beginners", "duration": 60, "max_participants": 15},
        {"time": "17:00", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "18:30", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "20:00", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "21:30", "name": "Yoga", "duration": 60, "max_participants": 15},
    ],
    1: [  # ВТОРНИК
        {"time": "08:00", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "09:30", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "11:30", "name": "Stretching", "duration": 60, "max_participants": 15},
        {"time": "12:30", "name": "Weightlifting", "duration": 60, "max_participants": 10},
        {"time": "15:00", "name": "Thai Boxing", "duration": 60, "max_participants": 15},
        {"time": "17:00", "name": "CrossFit Beginners", "duration": 60, "max_participants": 15},
        {"time": "18:00", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "19:30", "name": "Weightlifting", "duration": 60, "max_participants": 10},
        {"time": "20:30", "name": "CrossFit", "duration": 60, "max_participants": 12},
    ],
    2: [  # СРЕДА
        {"time": "08:00", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "09:30", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "12:30", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "14:00", "name": "CrossFit Beginners", "duration": 60, "max_participants": 15},
        {"time": "17:00", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "18:30", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "20:00", "name": "CrossFit", "duration": 60, "max_participants": 12},
    ],
    3: [  # ЧЕТВЕРГ
        {"time": "08:00", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "09:30", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "12:30", "name": "Weightlifting", "duration": 60, "max_participants": 10},
        {"time": "15:00", "name": "Thai Boxing", "duration": 60, "max_participants": 15},
        {"time": "17:00", "name": "CrossFit Beginners", "duration": 60, "max_participants": 15},
        {"time": "18:00", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "19:30", "name": "Weightlifting", "duration": 60, "max_participants": 10},
        {"time": "20:30", "name": "CrossFit", "duration": 60, "max_participants": 12},
    ],
    4: [  # ПЯТНИЦА
        {"time": "08:00", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "09:30", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "12:30", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "14:00", "name": "CrossFit Beginners", "duration": 60, "max_participants": 15},
        {"time": "17:00", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "18:30", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "20:00", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "21:30", "name": "Yoga", "duration": 60, "max_participants": 15},
    ],
    5: [  # СУББОТА
        {"time": "09:30", "name": "Yoga", "duration": 60, "max_participants": 15},
        {"time": "11:00", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "12:30", "name": "Weightlifting", "duration": 60, "max_participants": 10},
        {"time": "14:00", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "16:00", "name": "Thai Boxing", "duration": 60, "max_participants": 15},
    ],
    6: [  # ВОСКРЕСЕНЬЕ
        {"time": "11:00", "name": "CrossFit Beginners", "duration": 60, "max_participants": 15},
        {"time": "12:30", "name": "CrossFit", "duration": 60, "max_participants": 12},
        {"time": "14:00", "name": "CrossFit", "duration": 60, "max_participants": 12},
    ],
}


def main():
    """
    Этот файл используется веб-интерфейсом для массового создания расписания.
    
    Для создания расписания:
    1. Используйте веб-интерфейс: вкладка "⚙️ Создать расписание"
    2. Или запустите этот скрипт напрямую (не рекомендуется, лучше через веб)
    """
    print("=" * 60)
    print("📅 РАСПИСАНИЕ CROSSFIT ЗАЛА")
    print("=" * 60)
    
    weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    
    for day_num, day_name in enumerate(weekdays):
        workouts = WEEKLY_SCHEDULE.get(day_num, [])
        print(f"\n{day_name.upper()}:")
        if not workouts:
            print("  Выходной")
        else:
            for workout in workouts:
                print(f"  {workout['time']} - {workout['name']:20} ({workout['duration']} мин, макс: {workout['max_participants']} чел.)")
    
    print("\n" + "=" * 60)
    print(f"Всего слотов в неделю: {sum(len(w) for w in WEEKLY_SCHEDULE.values())}")
    print("=" * 60)
    
    print("\n💡 Для создания расписания используйте веб-интерфейс:")
    print("   http://localhost:8000")
    print("   Вкладка: ⚙️ Создать расписание")


if __name__ == "__main__":
    main()
