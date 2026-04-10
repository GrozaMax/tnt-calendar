# Architecture - Архитектура CrossFit Hub

## Общая архитектура

Проект построен на основе **многослойной архитектуры** с разделением на слои: Presentation (Handlers), Business Logic (Services), Data Access (Repositories), и Data Models.

### Архитектурная диаграмма

```
┌──────────────────────┐     ┌──────────────────────────────┐
│   Telegram Bot API   │     │   Браузер / HTTP клиент      │
└──────────┬───────────┘     └──────────────┬───────────────┘
           │                                │
           ▼                                ▼
┌──────────────────────┐     ┌──────────────────────────────┐
│  python-telegram-bot │     │  FastAPI (web/main.py)       │
│  Handlers + keyboards│     │  Jinja2 + static (SPA-lite)  │
│  Middleware (auth,   │     │  /api/* — тренировки, юзеры, │
│  locale)             │     │  настройки зала, auth        │
└──────────┬───────────┘     └──────────────┬───────────────┘
           │                                │
           └────────────────┬───────────────┘
                            ▼
           ┌────────────────────────────────────────┐
           │  Business Logic (Services)             │
           │  BookingService, WorkoutService,       │
           │  UserService, NotificationService, …   │
           └────────────────┬───────────────────────┘
                            ▼
           ┌────────────────────────────────────────┐
           │  Repositories                          │
           │  User, Workout, Booking, Settings,   │
           │  ScheduleTemplate, …                   │
           └────────────────┬───────────────────────┘
                            ▼
           ┌────────────────────────────────────────┐
           │  SQLAlchemy models → SQLite / PG       │
           └────────────────────────────────────────┘
```

## Структура исходного кода

```
/Users/maximgroza/PycharmProjects/tnt-calendar/
├── main.py                             # Точка входа бота
├── run_web.py                          # Запуск Uvicorn для веба
├── src/
│   ├── bot.py
│   ├── config.py
│   ├── constants.py                    # Дефолт/границы лимита записей в день
│   ├── models/
│   │   ├── user.py, workout.py, booking.py
│   │   ├── app_setting.py              # Ключ–значение (max_bookings_per_day)
│   │   └── schedule_template.py
│   ├── database/
│   │   ├── connection.py               # engine, init_db, точечные ALTER SQLite
│   │   ├── session.py
│   │   └── repositories/
│   │       ├── user_repository.py      # в т.ч. get_by_username
│   │       ├── workout_repository.py
│   │       ├── booking_repository.py
│   │       └── settings_repository.py
│   ├── services/
│   │   ├── booking_service.py          # лимит дня через SettingsRepository
│   │   ├── workout_service.py, user_service.py
│   │   └── notification_service.py
│   ├── handlers/, keyboards/, middleware/
│   ├── locales/                        # ru, en, ua, de, ge
│   └── utils/validators.py
├── web/
│   ├── main.py                         # FastAPI app, роуты /api/*
│   ├── config.py                       # WEB_LOGIN_SECRET, WEB_DEBUG, …
│   ├── api/                            # auth, workouts, users, business_settings, …
│   ├── templates/index.html
│   ├── static/app.js
│   └── utils/notifications.py
├── migrations/                         # Alembic (при необходимости)
├── tests/
│   ├── conftest.py                     # AsyncClient + ASGITransport, pytest_asyncio
│   ├── test_api.py, test_models.py, test_repositories.py, test_services.py
├── requirements.txt
├── alembic.ini
└── .env.example
```

## Модели данных

### User (Пользователь)
```python
class User:
    id: int (PK)
    telegram_id: int (unique, indexed)
    username: str (nullable)
    first_name: str
    last_name: str (nullable)
    role: Enum(ATHLETE, TRAINER, ADMIN)
    language: str (default='ru')
    notifications_enabled: bool  # исходящие уведомления в Telegram
    created_at: datetime
    updated_at: datetime
```

### Workout (Тренировка)
```python
class Workout:
    id: int (PK)
    name: str                    # Название тренировки
    description: str (nullable)  # Описание
    datetime: datetime           # Дата и время
    duration: int                # Длительность в минутах
    max_participants: int        # Макс. участников (default=999)
    trainer_id: int (nullable FK -> User)
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    trainer: User
    bookings: List[Booking]
    
    # Hybrid: current_participants — учитывает загрузку relationship bookings
    # (inspect.unloaded); для точного числа в async-сервисе —
    # get_current_participants_async(session)
```

### Booking (Запись)
```python
class Booking:
    id: int (PK)
    user_id: int (FK -> User)
    workout_id: int (FK -> Workout)
    status: Enum(ACTIVE, CANCELLED)
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    user: User
    workout: Workout
    
    # Unique constraint: (user_id, workout_id)
```

### AppSetting (настройки зала)
```python
class AppSetting:
    id: int (PK)
    key: str (unique)            # например "max_bookings_per_day"
    value: str                   # строковое значение (парсинг в сервисе)
```

## Ключевые технические решения

### 1. Система ролей (Role-Based Access Control)

**Enum для ролей:**
```python
class UserRole(enum.Enum):
    ATHLETE = "athlete"
    TRAINER = "trainer"
    ADMIN = "admin"
```

**Декоратор для проверки прав:**
```python
@role_required(UserRole.ADMIN)
async def admin_only_handler(update, context):
    # Только для админов
```

**Причина**: Чёткое разделение прав доступа, легко расширяется.

### 2. Repository Pattern

Абстракция доступа к данным через репозитории:
```python
class WorkoutRepository:
    async def get_by_id(self, workout_id: int) -> Workout
    async def get_by_date(self, date: datetime.date) -> List[Workout]
    async def create(self, workout_data: dict) -> Workout
    async def update(self, workout_id: int, data: dict) -> Workout
    async def delete(self, workout_id: int) -> bool
```

**Причина**: Изоляция бизнес-логики от деталей хранения данных.

### 3. Service Layer (Бизнес-логика)

Вся бизнес-логика в сервисах:
```python
class BookingService:
    async def create_booking(self, user_id: int, workout_id: int):
        # Проверка лимитов
        # Валидация времени
        # Создание записи
```

**Причина**: Переиспользование логики, легко тестировать.

### 4. Мультиязычность

**Менеджер локализации:**
```python
class LocaleManager:
    def get_text(self, key: str, lang: str) -> str
    def get_keyboard(self, key: str, lang: str) -> InlineKeyboardMarkup
```

**Использование:**
```python
text = locale.get_text('schedule.today', user.language)
```

**Причина**: Централизованное управление переводами.

### 5. Inline-клавиатуры с callback_data

**Структура callback_data:**
```
action:entity_id:additional_params

Примеры:
- "book:workout_123"     # Записаться на тренировку 123
- "cancel:booking_456"   # Отменить запись 456
- "schedule:today"       # Показать расписание на сегодня
```

**Причина**: Компактная передача данных, легко парсить.

### 6. Асинхронная работа с БД

SQLAlchemy с async поддержкой:
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

async with async_session() as session:
    result = await session.execute(query)
```

**Причина**: Неблокирующая работа с БД в асинхронном боте.

## Паттерны проектирования

### 1. Repository Pattern
Абстракция доступа к данным.

### 2. Service Layer Pattern
Бизнес-логика отделена от презентационного слоя.

### 3. Decorator Pattern
Проверка прав доступа через декораторы.

### 4. Factory Pattern
Создание клавиатур и сообщений на разных языках.

### 5. Singleton Pattern
Database connection pool, LocaleManager.

## Критические пути выполнения

### 1. Запись на тренировку (Атлет)

```
1. Выбор дня в пределах 7 дней от сегодня (прошедшие слоты «сегодня» скрыты)
2. WorkoutRepository / сервис — список тренировок на дату
3. Callback «Записаться» → BookingService.create_booking()
4. Валидация:
   - Лимит активных записей на календарный день (значение из app_settings,
     дефолт/диапазон в constants.py)
   - Время тренировки не в прошлом (validators)
   - Свободные места (get_current_participants_async + max_participants)
5. Создание Booking, при необходимости уведомления (с учётом notifications_enabled)
```

### 2. Бронирование слота (Тренер)

```
1. Trainer выбирает "🗓️ Забронировать слот"
2. Выбор даты через календарь
3. Выбор времени
4. Ввод названия тренировки
5. WorkoutService.create_workout()
6. Создание Workout в БД
7. Подтверждение: "✅ Слот забронирован"
```

### 3. Управление расписанием и пользователями (Админ)

**В боте:** сценарии админ-хендлеров (роли, просмотр и т.д.).

**В веб-панели:** CRUD тренировок, пользователей, шаблон расписания, картинка расписания, вкладка «Настройки зала» (`GET/PATCH /api/settings`) — в т.ч. `max_bookings_per_day`.

## Бизнес-правила (Business Rules)

### Правила записи:

1. **Лимит записей в день**: 
   - Число **активных** записей атлета на **календарный день** ограничено настройкой `max_bookings_per_day` в `app_settings` (дефолт и min/max в `src/constants.py`); читает `BookingService` через `SettingsRepository`.

2. **Временные ограничения**:
   - Нельзя записаться на тренировку в прошлом; выбор дня в UI — до 7 дней вперёд.
   - Проверка времени: валидаторы / `BookingService`.

3. **Лимит участников**:
   - Максимум участников на тренировке (default=999)
   - Проверка: `WorkoutService.has_free_slots(workout_id)`

4. **Уникальность записи**:
   - Один пользователь не может записаться на одну тренировку дважды
   - DB constraint: UNIQUE(user_id, workout_id)

### Права доступа:

1. **Athlete**:
   - Просмотр расписания
   - Запись/отмена своих записей
   - Просмотр своих записей

2. **Trainer** (+ все права Athlete):
   - Бронирование слотов
   - Просмотр списка участников своих классов
   - Добавление/удаление участников

3. **Admin** (+ все права Trainer):
   - Глобальное управление расписанием
   - Управление правами пользователей
   - Доступ ко всем тренировкам

## Взаимосвязи компонентов

```
Bot → Handlers → Services → Repositories → Models → Database
         ↓           ↓
    Keyboards   Validators
         ↓
   LocaleManager

FastAPI (web) → api routers → Services / Repositories → Models → Database
```

**Зависимости:**
- Handlers зависят от Services и Keyboards
- Веб-роутеры зависят от тех же сервисов и репозиториев (отдельные сессии БД в рамках запроса)
- Services зависят от Repositories и Validators
- Repositories зависят от Models
- LocaleManager — преимущественно бот; веб — шаблоны и статический JS

## Масштабируемость

### Горизонтальное масштабирование:
- Использование PostgreSQL вместо SQLite
- Connection pooling
- Redis для кэширования

### Вертикальное масштабирование:
- Оптимизация запросов к БД
- Индексы на часто используемые поля
- Eager loading для relationships

## Безопасность

1. **Бот**: идентификация по Telegram ID; авторизация ролей через middleware/декораторы.
2. **Веб**: вход `POST /api/auth/login` — логин (Telegram ID или username) + секрет **`WEB_LOGIN_SECRET`** из окружения (не хранить в клиентском JS); при `WEB_DEBUG` без секрета — только для разработки.
3. **Валидация входных данных**: Services / Pydantic в API.
4. **SQL Injection**: SQLAlchemy ORM.
5. **Секреты**: не коммитить `.env`; `.env.example` — плейсхолдеры.
6. **Rate Limiting**: по желанию на production.

## Производительность

### Оптимизации:

1. **Индексы БД**:
   - `User.telegram_id` (unique index)
   - `Workout.datetime` (index)
   - `Booking.(user_id, workout_id)` (composite index)

2. **Eager Loading**:
   ```python
   # Загрузка тренировки с тренером за один запрос
   workout = await session.get(
       Workout, workout_id, 
       options=[selectinload(Workout.trainer)]
   )
   ```

3. **Connection Pooling**:
   ```python
   engine = create_async_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=0
   )
   ```

## Тестирование

### Уровни тестирования:

1. **Unit / integration**: сервисы, репозитории, модели
2. **API**: FastAPI через `httpx` + `ASGITransport`

### Структура тестов (фактическая):
```
tests/
├── conftest.py           # async fixtures, httpx.AsyncClient + ASGITransport
├── test_api.py           # FastAPI (в т.ч. /api/settings)
├── test_models.py
├── test_repositories.py
└── test_services.py
```
Запуск: `pytest tests/` (плагин `pytest-asyncio` подключён в `conftest.py`).
