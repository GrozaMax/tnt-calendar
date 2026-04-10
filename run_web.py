#!/usr/bin/env python3
"""
Скрипт для запуска веб-интерфейса CrossFit Hub
"""

if __name__ == "__main__":
    import uvicorn
    from web.config import WebConfig
    
    print("🚀 Запуск веб-интерфейса TNT Admin panel...")
    print(f"📡 Адрес: http://{WebConfig.HOST}:{WebConfig.PORT}")
    print(f"📚 API документация: http://{WebConfig.HOST}:{WebConfig.PORT}/docs")
    print("\n💡 Для входа используйте:\n")
    print("   - Логин: Telegram ID (цифры) или ваш Telegram username (без @)")
    print("   - Секретный код из переменной окружения WEB_LOGIN_SECRET (см. .env.example)")
    print("\nДля остановки нажмите Ctrl+C\n")
    
    uvicorn.run(
        "web.main:app",
        host=WebConfig.HOST,
        port=WebConfig.PORT,
        reload=WebConfig.DEBUG,
        log_level="info"
    )

