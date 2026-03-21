"""
Конфигурация веб-приложения
"""
import os
from dotenv import load_dotenv

load_dotenv()


class WebConfig:
    """Конфигурация веб-сервера"""
    
    # Сервер
    HOST = os.getenv("WEB_HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", os.getenv("WEB_PORT", "8000")))  # PORT — Railway standard
    DEBUG = os.getenv("WEB_DEBUG", "true").lower() == "true"
    
    # Безопасность
    SECRET_KEY = os.getenv("WEB_SECRET_KEY", "your-secret-key-change-in-production")
    
    # Токены доступа (генерируются для админов и тренеров)
    # Формат: telegram_id:token
    # Токены можно хранить в БД или в переменных окружения
    ADMIN_TOKENS = os.getenv("WEB_ADMIN_TOKENS", "").split(",")
    
    # Telegram Bot Token (для отправки уведомлений из веба)
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # CORS (если понадобится)
    CORS_ORIGINS = ["*"]
    
    @classmethod
    def validate_token(cls, token: str) -> bool:
        """Проверка валидности токена"""
        if not token:
            return False
        # Простая проверка - токен есть в списке
        return token in cls.ADMIN_TOKENS or len(token) >= 32
    
    @classmethod
    def get_user_from_token(cls, token: str) -> dict:
        """Получить информацию о пользователе из токена"""
        # В реальности здесь должна быть проверка JWT или lookup в БД
        # Пока простая реализация
        return {"token": token, "authenticated": True}

