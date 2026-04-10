# TNT Calendar

Telegram-бот + веб-панель для управления расписанием и записью на тренировки в спортивном зале.

## Возможности

### Telegram-бот

**Атлеты:**
- Просмотр расписания на неделю вперёд (7 дней)
- Запись на тренировку / отмена записи
- Просмотр своих записей
- Настройки: язык (RU, UA, EN, DE, GE), включение/выключение уведомлений

**Тренеры:**
- Просмотр наполненности своих классов
- Добавление/удаление участников (Coach's Override)

**Администраторы:**
- Управление расписанием, загрузка картинки расписания
- Назначение ролей пользователям

### Веб-панель (FastAPI)

- CRUD тренировок: создание, редактирование, удаление, массовое создание по шаблону
- Управление пользователями: роли, индивидуальные пароли для входа в веб
- Шаблон недельного расписания
- Настройки зала: лимит записей атлета в день (настраиваемый)
- Загрузка картинки расписания

## Быстрый старт (локально)

**Требования:** Python 3.9+, токен бота от [@BotFather](https://t.me/BotFather).

```bash
git clone https://github.com/GrozaMax/tnt-calendar.git
cd tnt-calendar
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Заполните TELEGRAM_BOT_TOKEN и ADMIN_TELEGRAM_IDS в .env
```

Запуск:

```bash
python main.py       # бот
python run_web.py    # веб-панель (http://localhost:8000)
```

При первом запуске автоматически создаётся БД `crossfit_hub.db` с нужными таблицами.

## Деплой (Docker)

Два контейнера (бот + веб) из одного образа, общий volume для SQLite и загрузок.

```bash
git clone https://github.com/GrozaMax/tnt-calendar.git
cd tnt-calendar
bash setup.sh
```

Скрипт `setup.sh` установит Docker, спросит токен бота и ваш Telegram ID, сгенерирует пароли, соберёт и запустит контейнеры.

Обновление после мержа новых фич:

```bash
bash update.sh
```

Подробнее: [DEPLOY.md](DEPLOY.md).

## Переменные окружения

| Переменная | Описание |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Токен от @BotFather |
| `DATABASE_URL` | URL БД (SQLite или PostgreSQL) |
| `ADMIN_TELEGRAM_IDS` | Telegram ID супер-админов через запятую |
| `WEB_LOGIN_SECRET` | Общий пароль для входа в веб (fallback, если у пользователя нет индивидуального) |
| `WEB_DEBUG` | `true` / `false` |
| `UPLOADS_DIR` | Каталог загрузок (по умолчанию `uploads`) |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

Полный список с комментариями: [.env.example](.env.example).

## Структура проекта

```
tnt-calendar/
├── src/
│   ├── models/              # ORM: User, Workout, Booking, AppSetting, ScheduleTemplate
│   ├── database/
│   │   ├── connection.py    # engine, init_db, миграции SQLite
│   │   └── repositories/    # User, Workout, Booking, Settings
│   ├── services/            # BookingService, WorkoutService, NotificationService, ...
│   ├── handlers/            # Команды и callback для бота
│   ├── keyboards/           # Inline-клавиатуры
│   ├── locales/             # Переводы (ru, ua, en, de, ge)
│   ├── constants.py         # Дефолт/границы лимита записей
│   ├── bot.py               # Главный класс бота
│   └── config.py
├── web/
│   ├── main.py              # FastAPI app
│   ├── config.py            # WEB_LOGIN_SECRET, WEB_DEBUG, ...
│   ├── api/                 # auth, workouts, users, business_settings, schedule_*
│   ├── templates/
│   └── static/app.js
├── tests/                   # pytest + pytest-asyncio (50 тестов)
├── main.py                  # Точка входа бота
├── run_web.py               # Запуск веб-панели
├── setup.sh                 # Автоматический деплой на VPS
├── update.sh                # Обновление версии
├── Dockerfile
├── docker-compose.yml
└── DEPLOY.md
```

## Авторизация в веб-панели

Вход: Telegram ID (или username без `@`) + пароль.

- Если у пользователя задан **индивидуальный пароль** (вкладка «Пользователи» -> кнопка «Пароль»), проверяется он (SHA-256 + соль в БД).
- Иначе проверяется общий `WEB_LOGIN_SECRET` из `.env`.
- Доступ только для тренеров и админов.

## Бизнес-правила

- **Лимит записей в день:** настраивается админом в веб-панели (по умолчанию 2).
- **Запись:** только на будущие тренировки (не в прошлом), в пределах 7 дней.
- **Места:** `max_participants` на каждой тренировке.
- **Уникальность:** один пользователь — одна запись на тренировку.
- **Уведомления:** учитывают флаг `notifications_enabled` на пользователе.

## Тесты

```bash
pip install -r requirements.txt
pytest tests/ -v
```

50 тестов: модели, репозитории, сервисы, API (httpx + AsyncClient).

## Технологии

- [python-telegram-bot](https://python-telegram-bot.org/) 21.5
- [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn
- [SQLAlchemy](https://www.sqlalchemy.org/) 2.0 (async)
- SQLite (dev) / PostgreSQL (production)
- Docker + Docker Compose

## Лицензия

MIT
