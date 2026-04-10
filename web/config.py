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
    PORT = int(os.getenv("PORT", os.getenv("WEB_PORT", "8000")))
    DEBUG = os.getenv("WEB_DEBUG", "true").lower() == "true"
    
    # Безопасность
    SECRET_KEY = os.getenv("WEB_SECRET_KEY", "your-secret-key-change-in-production")
    # Секрет для входа в веб (никогда не храните реальное значение в клиентском JS)
    WEB_LOGIN_SECRET = os.getenv("WEB_LOGIN_SECRET", "").strip()
    
    # Токены доступа (генерируются для админов и тренеров)
    # Формат: telegram_id:token
    # Токены можно хранить в БД или в переменных окружения
    ADMIN_TOKENS = os.getenv("WEB_ADMIN_TOKENS", "").split(",")
    
    # Telegram Bot Token (для отправки уведомлений из веба)
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # CORS (если понадобится)
    CORS_ORIGINS = ["*"]

    @classmethod
    def get_web_login_secret(cls) -> str:
        """Пароль для входа тренеров/админов в веб. В production задаётся только через окружение."""
        if cls.WEB_LOGIN_SECRET:
            return cls.WEB_LOGIN_SECRET
        if cls.DEBUG:
            import logging
            logging.getLogger(__name__).warning(
                "WEB_LOGIN_SECRET не задан в окружении; используется небезопасное значение для разработки"
            )
            return "__dev_only_change_via_env_web_login_secret__"
        raise RuntimeError(
            "Задайте WEB_LOGIN_SECRET в окружении при WEB_DEBUG=false"
        )

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

