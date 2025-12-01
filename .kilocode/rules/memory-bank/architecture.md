# Architecture - Архитектура CrossFit Hub

## Общая архитектура

Проект построен на основе **многослойной архитектуры** с разделением на слои: Presentation (Handlers), Business Logic (Services), Data Access (Repositories), и Data Models.

### Архитектурная диаграмма

```
┌─────────────────────────────────────────┐
│         Telegram Bot API                │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      Application Layer                  │
│  - Routing commands/callbacks           │
│  - Authentication & Authorization       │
│  - Localization                         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Handlers Layer                  │
│  - Athlete handlers                     │
│  - Trainer handlers                     │
│  - Admin handlers                       │
│  - Inline keyboard callbacks            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      Business Logic Layer (Services)    │
│  - BookingService                       │
│  - WorkoutService                       │
│  - UserService                          │
│  - Validation & Business rules          │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Data Access Layer (Repositories)      │
│  - UserRepository                       │
│  - WorkoutRepository                    │
│  - BookingRepository                    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Data Models (ORM)               │
│  - User (id, telegram_id, role, lang)   │
│  - Workout (id, datetime, trainer_id)   │
│  - Booking (id, user_id, workout_id)    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Database (SQLite/PostgreSQL)    │
└─────────────────────────────────────────┘
```

## Структура исходного кода

```
/Users/maximgroza/PycharmProjects/tnt-calendar/
├── src/
│   ├── __init__.py
│   ├── bot.py                          # Главный класс бота
│   ├── config.py                       # Конфигурация
│   │
│   ├── models/                         # ORM модели (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── base.py                     # Base model
│   │   ├── user.py                     # User model
│   │   ├── workout.py                  # Workout model
│   │   └── booking.py                  # Booking model
│   │
│   ├── database/                       # Работа с БД
│   │   ├── __init__.py
│   │   ├── connection.py               # Database connection
│   │   ├── session.py                  # Session management
│   │   └── repositories/               # Repository pattern
│   │       ├── __init__.py
│   │       ├── user_repository.py
│   │       ├── workout_repository.py
│   │       └── booking_repository.py
│   │
│   ├── services/                       # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── user_service.py             # User management
│   │   ├── workout_service.py          # Workout management
│   │   └── booking_service.py          # Booking logic + validation
│   │
│   ├── handlers/                       # Обработчики команд
│   │   ├── __init__.py
│   │   ├── base.py                     # Общие команды (/start, /help)
│   │   ├── athlete.py                  # Обработчики для атлета
│   │   ├── trainer.py                  # Обработчики для тренера
│   │   └── admin.py                    # Обработчики для админа
│   │
│   ├── keyboards/                      # Inline клавиатуры
│   │   ├── __init__.py
│   │   ├── athlete_keyboards.py        # Клавиатуры для атлета
│   │   ├── trainer_keyboards.py        # Клавиатуры для тренера
│   │   └── admin_keyboards.py          # Клавиатуры для админа
│   │
│   ├── middleware/                     # Middleware
│   │   ├── __init__.py
│   │   ├── auth.py                     # Проверка прав доступа
│   │   └── locale.py                   # Мультиязычность
│   │
│   ├── locales/                        # Переводы
│   │   ├── __init__.py
│   │   ├── locale_manager.py           # Менеджер переводов
│   │   ├── ru.json                     # Русский
│   │   ├── ua.json                     # Украинский
│   │   ├── en.json                     # Английский
│   │   ├── de.json                     # Немецкий
│   │   └── ge.json                     # Грузинский
│   │
│   └── utils/                          # Утилиты
│       ├── __init__.py
│       ├── decorators.py               # Декораторы (role_required)
│       └── validators.py               # Валидаторы
│
├── migrations/                         # Alembic миграции
│   └── versions/
│
├── main.py                            # Точка входа
├── requirements.txt                   # Зависимости
├── alembic.ini                        # Конфигурация миграций
├── .env.example
├── .gitignore
└── README.md
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
    trainer_id: int (FK -> User)
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    trainer: User
    bookings: List[Booking]
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
1. User нажимает "📅 Расписание" → athlete_keyboards.main_menu()
2. User выбирает "Сегодня" → handler: show_schedule(date='today')
3. WorkoutService.get_workouts_by_date() → запрос к БД
4. Формирование списка с кнопками "Записаться"
5. User нажимает "Записаться" → callback: "book:workout_123"
6. handler: book_workout() → BookingService.create_booking()
7. Валидация:
   - Проверка лимита записей в день (max 2)
   - Проверка времени (только сегодня/завтра)
   - Проверка свободных мест
8. Если OK: создание Booking в БД
9. Ответ пользователю: "✅ Вы записаны!"
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

### 3. Управление расписанием (Админ)

```
1. Admin выбирает "⚙️ Управление расписанием"
2. Выбор действия (Создать/Редактировать/Удалить)
3. WorkoutService методы (CRUD)
4. Изменение БД
5. Подтверждение операции
```

## Бизнес-правила (Business Rules)

### Правила записи:

1. **Лимит записей в день**: 
   - Атлет может записаться максимум на 2 тренировки в один календарный день
   - Проверка: `BookingService.check_daily_limit(user_id, date)`

2. **Временные ограничения**:
   - Запись только на Сегодня (после текущего времени) и Завтра
   - Проверка: `BookingService.validate_booking_time(workout_datetime)`

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
```

**Зависимости:**
- Handlers зависят от Services и Keyboards
- Services зависят от Repositories и Validators
- Repositories зависят от Models
- Все компоненты могут использовать LocaleManager

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

1. **Аутентификация**: Через Telegram ID (встроенная)
2. **Авторизация**: Проверка ролей через декораторы
3. **Валидация входных данных**: На уровне Services
4. **SQL Injection**: Защита через SQLAlchemy ORM
5. **Rate Limiting**: Ограничение частоты запросов (будущая функция)

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

1. **Unit Tests**: Services, Validators
2. **Integration Tests**: Repositories
3. **End-to-End Tests**: Handlers (pytest-telegram-bot)

### Структура тестов:
```
tests/
├── unit/
│   ├── test_booking_service.py
│   └── test_validators.py
├── integration/
│   └── test_repositories.py
└── e2e/
    └── test_athlete_flow.py
```
