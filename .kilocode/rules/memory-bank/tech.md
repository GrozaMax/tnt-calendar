# Tech - Технологический стек

## Основные технологии

### Python 3.9+
**Версия**: 3.9 или выше (рекомендуется 3.11+)

**Причина выбора**:
- Поддержка современных возможностей языка (async/await, type hints)
- Широкая экосистема библиотек
- Отличная поддержка асинхронного программирования

### python-telegram-bot 21.5
**Официальная документация**: https://python-telegram-bot.org/

**Ключевые возможности**:
- Асинхронная архитектура на основе `asyncio`
- Полная поддержка Telegram Bot API
- Встроенные обработчики команд, сообщений, callback-запросов
- JobQueue для отложенных задач и напоминаний
- Удобная система middleware

**Основные компоненты**:
- `Application` - главный класс приложения
- `CommandHandler` - обработчик команд
- `MessageHandler` - обработчик сообщений
- `CallbackQueryHandler` - обработчик inline-кнопок
- `ContextTypes` - типизация контекста

### python-dotenv 1.0.1
**Назначение**: Управление переменными окружения

**Использование**:
```python
from dotenv import load_dotenv
load_dotenv()  # Загружает .env файл
```

**Причина выбора**: Стандарт для управления конфигурацией в Python приложениях

### aiohttp 3.10.5
**Назначение**: Асинхронный HTTP клиент/сервер

**Использование**: 
- Потенциально для webhooks
- Интеграция с внешними API
- Асинхронные HTTP запросы

## Структура зависимостей

```
requirements.txt:
├── python-telegram-bot==21.5    # Основная библиотека
├── python-dotenv==1.0.1         # Конфигурация
└── aiohttp==3.10.5              # HTTP клиент
```

## Настройка окружения разработки

### 1. Создание виртуального окружения

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Создать файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

Заполнить переменные:
```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
ADMIN_IDS=123456789,987654321
LOG_LEVEL=INFO
```

## Конфигурация проекта

### Переменные окружения

| Переменная | Обязательна | Описание | Пример |
|-----------|-------------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Токен от @BotFather | `123456:ABC-DEF...` |
| `ADMIN_IDS` | ❌ | ID администраторов (через запятую) | `123456789,987654321` |
| `LOG_LEVEL` | ❌ | Уровень логирования | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### Логирование

Настроено через стандартный модуль `logging`:
```python
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, Config.LOG_LEVEL)
)
```

**Уровни логирования**:
- `DEBUG` - детальная информация для отладки
- `INFO` - общая информация о работе (по умолчанию)
- `WARNING` - предупреждения
- `ERROR` - ошибки

## Технические ограничения

### Python версия
- **Минимум**: Python 3.9
- **Рекомендуется**: Python 3.11+
- **Причина**: `python-telegram-bot` требует 3.9+ для async/await

### Telegram Bot API
- **Rate limits**: 30 сообщений/сек на бота
- **Размер сообщения**: до 4096 символов
- **Размер файла**: до 50 МБ
- **Timeout**: рекомендуется 30 секунд для long polling

### Асинхронность
- Все обработчики должны быть `async def`
- Использование `await` для всех IO операций
- Нельзя использовать блокирующие операции в обработчиках

## Инструменты разработки

### Рекомендуемые IDE
- **PyCharm** (текущая среда разработки)
- VS Code с расширением Python
- Любая IDE с поддержкой Python 3.9+

### Полезные команды

```bash
# Запуск бота
python main.py

# Установка зависимостей
pip install -r requirements.txt

# Обновление зависимостей
pip install --upgrade -r requirements.txt

# Проверка версии Python
python --version
```

## Будущие технологии (планируется)

### База данных
**Варианты**:
1. **SQLite** - для простых случаев, встроенная БД
2. **PostgreSQL** - для production, масштабируемость
3. **SQLAlchemy** - ORM для работы с БД

### Тестирование
- `pytest` - фреймворк для тестирования
- `pytest-asyncio` - поддержка async тестов
- `pytest-cov` - покрытие кода тестами

### Линтеры и форматтеры
- `black` - автоформатирование кода
- `flake8` - проверка стиля кода
- `mypy` - статическая типизация

### CI/CD
- GitHub Actions для автоматизации
- Docker для контейнеризации
- Docker Compose для локальной разработки

## Паттерны использования инструментов

### Async/Await
```python
# Правильно
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello")

# Неправильно - блокирующий вызов
def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.reply_text("Hello")  # Не будет работать!
```

### Обработка ошибок
```python
try:
    await some_async_operation()
except Exception as e:
    logger.error(f"Error: {e}")
    await update.message.reply_text("Произошла ошибка")
```

### Логирование
```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Детальная информация")
logger.info("Общая информация")
logger.warning("Предупреждение")
logger.error("Ошибка")
```

## Получение Telegram Bot Token

1. Открыть [@BotFather](https://t.me/BotFather) в Telegram
2. Отправить команду `/newbot`
3. Следовать инструкциям (имя бота, username)
4. Получить токен вида: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`
5. Добавить токен в `.env` файл

## Безопасность

### Хранение токенов
- ✅ Хранить в `.env` файле
- ✅ Добавить `.env` в `.gitignore`
- ❌ Никогда не коммитить токены в git
- ❌ Не хранить токены в коде

### Права доступа
- Использовать `ADMIN_IDS` для ограничения доступа к админ-командам
- Валидировать все пользовательские вводы
- Ограничивать частоту запросов от одного пользователя

## Производительность

### Рекомендации
- Использовать `async/await` для всех IO операций
- Избегать блокирующих операций в обработчиках
- Кэшировать часто используемые данные
- Использовать connection pooling для БД (когда будет добавлена)

### Мониторинг
- Логировать все ошибки
- Отслеживать время ответа
- Мониторить использование памяти
- Следить за rate limits Telegram API

