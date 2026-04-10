# Tech - Технологический стек CrossFit Hub

## Основные технологии

### Python 3.9+
**Версия**: 3.9 или выше (рекомендуется 3.11+)

**Причина выбора**:
- Поддержка современных возможностей (async/await, type hints, pattern matching)
- Широкая экосистема для работы с БД и ботами
- Отличная поддержка асинхронного программирования

### python-telegram-bot 21.5
**Официальная документация**: https://python-telegram-bot.org/

**Ключевые возможности**:
- Асинхронная архитектура на `asyncio`
- Полная поддержка Telegram Bot API
- CommandHandler, CallbackQueryHandler для обработки событий
- ConversationHandler для многошаговых диалогов
- JobQueue для отложенных задач

### SQLAlchemy 2.0+ (Async)
**Официальная документация**: https://docs.sqlalchemy.org/

**Назначение**: ORM для работы с базой данных

**Ключевые возможности**:
- Асинхронная поддержка (asyncio)
- Декларативные модели
- Relationships и lazy/eager loading
- Мощный query builder
- Миграции через Alembic

**Пример использования**:
```python
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user(session: AsyncSession, telegram_id: int):
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()
```

### Alembic
**Назначение**: Миграции базы данных

**Использование**:
```bash
# Создание миграции
alembic revision --autogenerate -m "Add user table"

# Применение миграций
alembic upgrade head
```

### SQLite / PostgreSQL
**SQLite**: Для разработки и малых инсталляций
**PostgreSQL**: Для production

**Текущее решение**: SQLite для начала, легко мигрировать на PostgreSQL

### python-dotenv 1.0.1
**Назначение**: Управление переменными окружения

### aiohttp 3.10.5
**Назначение**: Асинхронный HTTP клиент (для будущих интеграций)

## Структура зависимостей

Актуальный список — в корневом `requirements.txt`. Кратко:

```
python-telegram-bot==21.5
sqlalchemy[asyncio]==2.0.36
alembic==1.13.0
aiosqlite==0.19.0
asyncpg==0.29.0
python-dotenv==1.0.1
aiohttp==3.10.5
python-multipart==0.0.9

# Web
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.9.0

# Testing
pytest==7.4.3
pytest-asyncio==0.23.8
pytest-cov==4.1.0
httpx==0.27.0
faker==20.1.0
```

## Настройка окружения разработки

### 1. Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# или
venv\Scripts\activate  # Windows
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Создать файл `.env` (ориентир — `.env.example` в репозитории):
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_URL=sqlite+aiosqlite:///./crossfit_hub.db
ADMIN_TELEGRAM_IDS=123456789,987654321
LOG_LEVEL=INFO

# Веб-панель
WEB_LOGIN_SECRET=your_long_random_secret
WEB_DEBUG=true
# WEB_HOST, WEB_PORT / PORT, WEB_SECRET_KEY, WEB_ADMIN_TOKENS — см. web/config.py
```

### 4. Инициализация базы данных

```bash
# Инициализация Alembic
alembic init migrations

# Создание первой миграции
alembic revision --autogenerate -m "Initial schema"

# Применение миграций
alembic upgrade head
```

## Конфигурация проекта

### Переменные окружения

| Переменная | Обязательна | Описание | Пример |
|-----------|-------------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Токен от @BotFather | `123456:ABC-DEF...` |
| `DATABASE_URL` | ✅ | URL подключения к БД | `sqlite+aiosqlite:///./db.sqlite` |
| `ADMIN_TELEGRAM_IDS` | ❌ | ID супер-админов (через запятую) | `123456789,987654321` |
| `LOG_LEVEL` | ❌ | Уровень логирования | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `WEB_LOGIN_SECRET` | ✅ в prod | Секрет для входа в веб (логин + код) | длинная случайная строка |
| `WEB_DEBUG` | ❌ | `true`/`false`; при `false` без `WEB_LOGIN_SECRET` приложение не стартует безопасно | `true` локально |
| `WEB_HOST`, `WEB_PORT` / `PORT` | ❌ | Хост и порт Uvicorn | `0.0.0.0`, `8000` |
| `WEB_SECRET_KEY`, `WEB_ADMIN_TOKENS` | ❌ | Доп. настройки веба | см. `web/config.py` |

### Структура базы данных

**SQLite для разработки** (имя файла задаётся `DATABASE_URL`):
```
*.db
├── users              # в т.ч. notifications_enabled
├── workouts           # trainer_id может быть NULL
├── bookings
├── app_settings       # ключ–значение (max_bookings_per_day)
└── …                  # schedule_templates и др. по мере эволюции схемы
```

**Упрощённая схема** (детали — модели SQLAlchemy и `connection.py`):
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255),
    role VARCHAR(50) NOT NULL,  -- ATHLETE, TRAINER, ADMIN
    language VARCHAR(5) DEFAULT 'ru',
    notifications_enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workouts (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    datetime TIMESTAMP NOT NULL,
    duration INTEGER DEFAULT 60,
    max_participants INTEGER DEFAULT 999,
    trainer_id INTEGER REFERENCES users(id),  -- nullable в актуальной схеме
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bookings (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    workout_id INTEGER REFERENCES workouts(id),
    status VARCHAR(50) NOT NULL,  -- ACTIVE, CANCELLED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, workout_id)
);

CREATE TABLE app_settings (
    id INTEGER PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_workouts_datetime ON workouts(datetime);
CREATE INDEX idx_bookings_user_id ON bookings(user_id);
CREATE INDEX idx_bookings_workout_id ON bookings(workout_id);
```

## Мультиязычность

### Структура переводов

Файлы JSON в `src/locales/`:

**ru.json** (пример):
```json
{
  "menu": {
    "main": "🏠 Главное меню",
    "schedule": "📅 Расписание",
    "my_bookings": "📋 Мои записи",
    "settings": "⚙️ Настройки"
  },
  "schedule": {
    "today": "Сегодня",
    "tomorrow": "Завтра",
    "no_workouts": "На этот день тренировок нет",
    "booked": "✅ Записались: {count}/{max}"
  },
  "booking": {
    "success": "✅ Вы успешно записались на тренировку!",
    "limit_reached": "❌ Вы уже записаны на 2 тренировки в этот день",
    "no_slots": "❌ Свободных мест нет"
  }
}
```

### Использование:

```python
from src.locales import LocaleManager

locale = LocaleManager()
text = locale.get('booking.success', user.language)
# → "✅ Вы успешно записались на тренировку!"

# С параметрами
text = locale.get('schedule.booked', user.language, count=5, max=12)
# → "✅ Записались: 5/12"
```

## Инструменты разработки

### Рекомендуемые IDE
- **PyCharm Professional** (текущая среда)
- VS Code с расширениями (Python, SQLite Viewer)

### Линтеры и форматтеры (опционально)

```bash
# Для production рекомендуется добавить:
pip install black flake8 mypy pytest pytest-asyncio

# Использование
black src/
flake8 src/
mypy src/
pytest tests/
```

### Полезные команды

```bash
# Запуск бота
python main.py

# Запуск веб-панели (FastAPI)
python run_web.py

# Создание миграции
alembic revision --autogenerate -m "Description"

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1

# Просмотр БД (SQLite)
sqlite3 crossfit_hub.db

# Тесты
pytest tests/ -v
```

## Паттерны использования

### 1. Асинхронная работа с БД

```python
from src.database import get_session

async def example_handler(update, context):
    async with get_session() as session:
        user = await UserRepository(session).get_by_telegram_id(
            update.effective_user.id
        )
        # работа с user
        await session.commit()
```

### 2. Обработка callback запросов

```python
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Важно! Убирает "часики" на кнопке
    
    # Парсинг callback_data
    action, entity_id = query.data.split(':')
    
    if action == 'book':
        await book_workout(query, int(entity_id))
```

### 3. Проверка прав доступа

```python
from src.utils.decorators import role_required
from src.models import UserRole

@role_required(UserRole.TRAINER)
async def trainer_only_handler(update, context):
    # Доступно только тренерам
    pass
```

### 4. Inline-клавиатуры

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def create_schedule_keyboard(workouts, lang='ru'):
    keyboard = []
    for workout in workouts:
        button = InlineKeyboardButton(
            text=f"{workout.datetime.strftime('%H:%M')} - {workout.name}",
            callback_data=f"book:{workout.id}"
        )
        keyboard.append([button])
    
    return InlineKeyboardMarkup(keyboard)
```

### 5. ConversationHandler (многошаговые диалоги)

```python
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters

# Состояния
SELECT_DATE, SELECT_TIME, CONFIRM = range(3)

conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('book_slot', start_booking)],
    states={
        SELECT_DATE: [CallbackQueryHandler(date_selected)],
        SELECT_TIME: [CallbackQueryHandler(time_selected)],
        CONFIRM: [CallbackQueryHandler(confirm_booking)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)
```

## Логирование

### Конфигурация

```python
import logging
from src.config import Config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, Config.LOG_LEVEL)
)

logger = logging.getLogger(__name__)

# Использование
logger.info("User %s booked workout %s", user_id, workout_id)
logger.error("Failed to create booking: %s", error)
```

## Безопасность

### Хранение токенов
- ✅ Хранить в `.env` файле
- ✅ Добавить `.env` в `.gitignore`
- ❌ Никогда не коммитить токены

### SQL Injection
- ✅ Использовать SQLAlchemy ORM (защита из коробки)
- ❌ Не использовать сырые SQL запросы с пользовательским вводом

### Валидация данных
```python
from src.utils.validators import validate_workout_time, validate_booking

# Всегда валидировать пользовательский ввод
if not validate_workout_time(datetime):
    raise ValueError("Invalid workout time")
```

## Производительность

### Оптимизация запросов

```python
# ❌ Плохо: N+1 запросов
workouts = await workout_repo.get_all()
for workout in workouts:
    trainer = await user_repo.get_by_id(workout.trainer_id)  # N запросов!

# ✅ Хорошо: Eager loading
from sqlalchemy.orm import selectinload

workouts = await session.execute(
    select(Workout).options(selectinload(Workout.trainer))
)
workouts = workouts.scalars().all()
```

### Индексы БД

Всегда создавать индексы для:
- Foreign keys
- Часто используемые в WHERE поля
- Unique constraints

```python
class User(Base):
    telegram_id = Column(Integer, unique=True, index=True)  # Индекс!
```

### Connection Pooling

```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # True для отладки SQL запросов
    pool_size=20,
    max_overflow=0,
)
```

## Тестирование

### Структура тестов

```
tests/
├── conftest.py              # pytest_asyncio, AsyncClient + ASGITransport
├── test_api.py              # FastAPI (в т.ч. /api/settings)
├── test_models.py
├── test_repositories.py
└── test_services.py
```

### Пример теста

```python
import pytest
from src.services import BookingService

@pytest.mark.asyncio
async def test_create_booking_success(db_session, sample_user, sample_workout):
    service = BookingService(db_session)
    
    booking = await service.create_booking(
        user_id=sample_user.id,
        workout_id=sample_workout.id
    )
    
    assert booking.user_id == sample_user.id
    assert booking.status == "ACTIVE"
```

Для HTTP API используется `httpx.AsyncClient` с `ASGITransport(app=...)` (см. `tests/conftest.py`).

## Миграция на Production

### Переход на PostgreSQL

1. Установить драйвер:
```bash
pip install asyncpg
```

2. Изменить `DATABASE_URL`:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/crossfit_hub
```

3. Применить миграции:
```bash
alembic upgrade head
```

### Deployment (Docker)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

## Мониторинг

### Логи
- Использовать структурированные логи
- Отправлять критические ошибки в Telegram канал админам

### Метрики (будущее)
- Количество активных пользователей
- Количество записей в день
- Популярные времена тренировок

## Получение Telegram Bot Token

1. Открыть [@BotFather](https://t.me/BotFather)
2. Отправить `/newbot`
3. Следовать инструкциям
4. Получить токен и добавить в `.env`

## Рекомендации по кодированию

### Type Hints
Всегда использовать type hints:
```python
async def get_user(session: AsyncSession, user_id: int) -> User | None:
    ...
```

### Docstrings
Документировать публичные функции:
```python
async def create_booking(user_id: int, workout_id: int) -> Booking:
    """
    Создаёт запись на тренировку.
    
    Args:
        user_id: ID пользователя
        workout_id: ID тренировки
    
    Returns:
        Созданная запись
    
    Raises:
        ValueError: Если лимит записей превышен
    """
```

### Именование
- Классы: `PascalCase`
- Функции/переменные: `snake_case`
- Константы: `UPPER_SNAKE_CASE`
- Private методы: `_leading_underscore`
