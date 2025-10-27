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
    
    # Admin IDs
    ADMIN_IDS = [
        int(admin_id.strip()) 
        for admin_id in os.getenv('ADMIN_IDS', '').split(',') 
        if admin_id.strip()
    ]
    
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
        return True

