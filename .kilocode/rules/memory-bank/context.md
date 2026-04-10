# Context - Текущее состояние проекта

## Текущий фокус

Гибрид **Telegram-бот + веб (FastAPI)** для зала (в репозитории также фигурирует название TNT Admin panel). Бот — атлеты и просмотр для тренеров/админов; создание/редактирование расписания и пользователей — в вебе.

**Последнее обновление Memory Bank:** апрель 2026 (синхронизация с кодом после доработок TODO, тестов и модели `Workout`).

## Недавние изменения (актуальный код)

- **Лимит записей атлета в календарный день**: значение в БД (`app_settings`, ключ `max_bookings_per_day`), дефолт и диапазон в `src/constants.py`; читает `BookingService`; админ меняет во вкладке веба «Настройки зала» и через `GET/PATCH /api/settings`.
- **Веб-вход**: `POST /api/auth/login` с полями `login` (Telegram ID **или** username без `@`) и `secret_code` из **`WEB_LOGIN_SECRET`** (в `.env`, не в JS). При пустом секрете и `WEB_DEBUG=true` — dev-заглушка с предупреждением в лог.
- **Пользователь**: `notifications_enabled` (bool); в боте «Настройки» — переключатель; исходящие уведомления атлетам/тренерам учитывают флаг.
- **`Workout.current_participants`**: Python-геттер hybrid использует `sqlalchemy.inspect(self).unloaded` для проверки загрузки `bookings` (совместимо с `selectinload` в репозитории); для записи в сервисе используется **`get_current_participants_async(session)`**.
- **Миграции SQLite** в `connection.py`: nullable `trainer_id`, колонка `users.notifications_enabled`, таблица `app_settings`; при `init_db` — дефолт для лимита дня.
- **Тесты**: `pytest-asyncio` 0.23.x; API-тесты на `httpx.AsyncClient` + `ASGITransport`; 46 тестов зелёные; модельные тесты `Workout` используют `selectinload` + `populate_existing=True` где нужно обойти identity map.
- **`.env.example`**: только плейсхолдеры, без реальных секретов.

## Структура (кратко)

| Область | Пути |
|--------|------|
| Бот | `main.py`, `src/bot.py`, `src/handlers/`, `src/keyboards/` |
| Веб | `web/main.py`, `web/api/` (`auth`, `workouts`, `users`, `business_settings`, …), `web/static/app.js`, `web/templates/index.html` |
| Модели | `src/models/` (`user`, `workout`, `booking`, `app_setting`, `schedule_template`) |
| Репозитории | `src/database/repositories/` (+ `settings_repository.py`) |
| Константы лимита | `src/constants.py` |

## Атлет: расписание и запись (фактическое поведение)

- Выбор дня: **7 дней от сегодня**; на «сегодня» не показываются прошедшие по времени тренировки.
- Валидация времени записи: **не в прошлом** (`validate_booking_time`); лимит мест — `get_current_participants_async` + `max_participants`.

## Следующие шаги (идеи)

- JWT / усиление авторизации веба, CORS/rate limit для production.
- Alembic вместо точечных `ALTER` в `connection.py` при росте схемы.
- Напоминания по расписанию (JobQueue), если понадобятся сверх текущих push-уведомлений.

## Запуск

```bash
pip install -r requirements.txt
cp .env.example .env   # заполнить TELEGRAM_BOT_TOKEN, WEB_LOGIN_SECRET, …
python main.py         # бот
python run_web.py      # веб
```

## Примечание по `brief.md`

Файл `brief.md` вручную не менялся при этом обновлении. Имеет смысл при необходимости **вручную** согласовать формулировки с продуктом: дневной лимит **настраиваемый** (не фиксированные «2»), календарь в боте — **неделя**, а не только «сегодня/завтра».
