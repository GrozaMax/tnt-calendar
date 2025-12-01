# CrossFit Hub Bot 🏋️‍♂️

Telegram бот для управления расписанием и бронированием тренировок в кроссфит-зале.

## 🎯 Возможности

### Для Атлетов:
- 📅 Просмотр расписания на сегодня и завтра
- ✅ Запись на тренировки (максимум 2 в день)
- ❌ Отмена записи
- 📋 Просмотр своих записей

### Для Тренеров (в разработке):
- 🗓️ Бронирование слотов под свои тренировки
- 👥 Просмотр списка участников
- ➕ Добавление/удаление участников

### Для Администраторов (в разработке):
- ⚙️ Управление расписанием
- 👤 Управление правами пользователей

## 🚀 Быстрый старт

### Требования

- Python 3.9 или выше
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))

### Установка

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd tnt-calendar
```

2. **Создайте виртуальное окружение:**
```bash
python3 -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

3. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

4. **Настройте переменные окружения:**
```bash
cp .env.example .env
```

Отредактируйте файл `.env` и добавьте ваш Telegram Bot Token:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_URL=sqlite+aiosqlite:///./crossfit_hub.db
ADMIN_TELEGRAM_IDS=your_telegram_id
LOG_LEVEL=INFO
```

### Запуск

```bash
python main.py
```

При первом запуске автоматически создастся база данных `crossfit_hub.db`.

## 📋 Основные команды

- `/start` - Начать работу с ботом и открыть главное меню
- `/help` - Показать справку по использованию

Все остальные функции доступны через интерактивное меню с кнопками.

## 🏗️ Структура проекта

```
tnt-calendar/
├── src/
│   ├── models/                 # ORM модели (User, Workout, Booking)
│   ├── database/               # Подключение к БД и репозитории
│   ├── services/               # Бизнес-логика
│   ├── handlers/               # Обработчики команд и callback
│   ├── keyboards/              # Inline-клавиатуры
│   ├── locales/                # Переводы (RU, UA, EN, DE, GE)
│   ├── utils/                  # Утилиты и валидаторы
│   ├── bot.py                  # Главный класс бота
│   └── config.py               # Конфигурация
├── main.py                     # Точка входа
├── requirements.txt            # Зависимости
└── README.md                   # Документация
```

## 🗄️ База данных

Проект использует SQLAlchemy ORM с поддержкой асинхронности.

### Модели:

**User** (Пользователь):
- `telegram_id` - Telegram ID пользователя
- `role` - Роль (ATHLETE, TRAINER, ADMIN)
- `language` - Предпочитаемый язык

**Workout** (Тренировка):
- `name` - Название тренировки
- `datetime` - Дата и время
- `trainer_id` - ID тренера
- `max_participants` - Максимум участников

**Booking** (Запись):
- `user_id` - ID пользователя
- `workout_id` - ID тренировки
- `status` - Статус (ACTIVE, CANCELLED)

### Миграции с Alembic (опционально)

```bash
# Инициализация
alembic init migrations

# Создание миграции
alembic revision --autogenerate -m "Description"

# Применение миграций
alembic upgrade head
```

## 📝 Бизнес-правила

### Ограничения для записи:
1. **Временные рамки**: Запись возможна только на Сегодня (после текущего времени) и Завтра
2. **Лимит записей**: Максимум 2 записи на один календарный день
3. **Лимит участников**: Настраивается для каждой тренировки (по умолчанию 999)

### Роли пользователей:
- **ATHLETE** (Атлет): Базовые функции просмотра и записи
- **TRAINER** (Тренер): + Управление своими классами
- **ADMIN** (Админ): Полный доступ к системе

## 🌐 Мультиязычность

Бот поддерживает 5 языков:
- 🇷🇺 Русский (ru) - **реализован**
- 🇺🇦 Украинский (ua) - в разработке
- 🇬🇧 Английский (en) - в разработке
- 🇩🇪 Немецкий (de) - в разработке
- 🇬🇪 Грузинский (ge) - в разработке

Переводы хранятся в `src/locales/*.json`.

## 🛠️ Разработка

### Добавление новых переводов

1. Откройте `src/locales/ru.json`
2. Добавьте новый ключ
3. Создайте соответствующие файлы для других языков

### Добавление новых обработчиков

1. Создайте функцию в `src/handlers/`
2. Зарегистрируйте её в `src/bot.py` в методе `_register_handlers()`

### Логирование

Уровень логирования настраивается в `.env`:
```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

## 📊 Тестовые данные

Для тестирования можно создать тестовые тренировки через Python:

```python
import asyncio
from datetime import datetime, timedelta
from src.database import get_session
from src.database.repositories import UserRepository, WorkoutRepository
from src.models import UserRole

async def create_test_data():
    async with get_session() as session:
        user_repo = UserRepository(session)
        workout_repo = WorkoutRepository(session)
        
        # Создать тренера
        trainer, _ = await user_repo.get_or_create(
            telegram_id=123456789,
            first_name="Тренер",
            last_name="Иванов"
        )
        trainer.role = UserRole.TRAINER
        
        # Создать тренировки
        today = datetime.now().replace(hour=18, minute=0, second=0)
        await workout_repo.create(
            name="CrossFit WOD",
            datetime=today,
            trainer_id=trainer.id,
            duration=60,
            max_participants=12
        )
        
        tomorrow = today + timedelta(days=1)
        await workout_repo.create(
            name="Olympic Lifting",
            datetime=tomorrow,
            trainer_id=trainer.id,
            duration=90,
            max_participants=8
        )
        
        await session.commit()
        print("✅ Тестовые данные созданы!")

# Запуск
asyncio.run(create_test_data())
```

## 🔐 Безопасность

- ✅ Токен хранится в `.env` (не коммитится в git)
- ✅ Валидация всех пользовательских вводов
- ✅ Проверка прав доступа через декораторы
- ✅ SQLAlchemy ORM защищает от SQL Injection

## 📄 Лицензия

MIT

## 👨‍💻 Разработка

Разработано с использованием:
- [python-telegram-bot](https://python-telegram-bot.org/) v21.5
- [SQLAlchemy](https://www.sqlalchemy.org/) v2.0+
- [Alembic](https://alembic.sqlalchemy.org/)

## 📞 Поддержка

Для вопросов и предложений создавайте Issues в репозитории.

---

**CrossFit Hub Bot** - Ваш персональный помощник в управлении тренировками! 💪
