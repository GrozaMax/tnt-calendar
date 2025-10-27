# TNT Calendar Bot

Telegram бот для управления календарем, написанный на Python.

## 🚀 Быстрый старт

### Требования

- Python 3.9 или выше
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))

### Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd tnt-calendar
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте переменные окружения:
```bash
cp .env.example .env
```

Отредактируйте файл `.env` и добавьте ваш Telegram Bot Token:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### Запуск

```bash
python main.py
```

## 📋 Доступные команды

- `/start` - Начать работу с ботом
- `/help` - Показать справку
- `/calendar` - Открыть календарь (в разработке)

## 🏗️ Структура проекта

```
tnt-calendar/
├── src/
│   ├── __init__.py
│   ├── bot.py              # Главный модуль бота
│   ├── config.py           # Конфигурация
│   └── handlers/           # Обработчики команд
│       ├── __init__.py
│       └── base.py         # Базовые команды
├── main.py                 # Точка входа
├── requirements.txt        # Зависимости
├── .env.example           # Пример конфигурации
├── .gitignore
└── README.md
```

## 🛠️ Разработка

### Добавление новых команд

1. Создайте обработчик в `src/handlers/`
2. Зарегистрируйте его в `src/bot.py` в методе `_register_handlers()`

### Логирование

Уровень логирования можно настроить в `.env`:
```
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

## 📝 Технологии

- [python-telegram-bot](https://python-telegram-bot.org/) - Асинхронная библиотека для Telegram Bot API
- [python-dotenv](https://github.com/theskumar/python-dotenv) - Управление переменными окружения
- [aiohttp](https://docs.aiohttp.org/) - Асинхронный HTTP клиент

## 📄 Лицензия

MIT

