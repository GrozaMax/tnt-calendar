"""
Конфигурация бота
"""
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()


class Config:
    """Класс конфигурации бота"""
    
    # Telegram Bot Token
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Admin Telegram IDs
    ADMIN_TELEGRAM_IDS = [
        int(admin_id.strip()) 
        for admin_id in os.getenv('ADMIN_TELEGRAM_IDS', '').split(',') 
        if admin_id.strip()
    ]
    
    # Database — Railway выдаёт postgresql://, конвертируем в asyncpg
    _raw_db_url = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///./crossfit_hub.db')
    DATABASE_URL = (
        _raw_db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        if _raw_db_url.startswith('postgresql://') else _raw_db_url
    )
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls):
        """Валидация конфигурации"""
        if not cls.BOT_TOKEN:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN не установлен. "
                "Пожалуйста, создайте файл .env на основе .env.example"
            )
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL не установлен")
        return True

