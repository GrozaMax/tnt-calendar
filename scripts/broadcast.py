import asyncio
import os
import sys
import logging
from telegram import Bot
from telegram.error import TelegramError

# Добавляем корневую папку в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import get_session
from src.database.repositories import UserRepository
from src.config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def broadcast_message(message: str):
    bot = Bot(token=Config.BOT_TOKEN)
    
    async with get_session() as session:
        user_repo = UserRepository(session)
        users = await user_repo.get_all()
    
    success_count = 0
    fail_count = 0
    
    logger.info(f"Начинаем рассылку для {len(users)} пользователей...")
    
    for user in users:
        # Можно проверять notifications_enabled или роль, но рассылка важных обновлений обычно идет всем
        if not user.telegram_id:
            continue
            
        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            success_count += 1
            logger.info(f"✅ Отправлено {user.full_name} ({user.telegram_id})")
        except TelegramError as e:
            fail_count += 1
            logger.warning(f"❌ Ошибка отправки {user.full_name} ({user.telegram_id}): {e}")
            
        # Пауза, чтобы не словить спам-блок от Telegram (обычно ~30 сообщений в секунду лимит, но лучше перестраховаться)
        await asyncio.sleep(0.1)

    logger.info("====================================")
    logger.info(f"Рассылка завершена! Успешно: {success_count}, Ошибок: {fail_count}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Рассылка сообщений пользователям бота")
    parser.add_argument("--file", type=str, help="Путь к файлу с текстом сообщения (.txt, .md)")
    
    args = parser.parse_args()
    
    if args.file:
        if not os.path.exists(args.file):
            print(f"Файл {args.file} не найден!")
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            message_text = f.read()
    else:
        print("Введите текст сообщения (для завершения введите EOF на новой строке, либо нажмите Ctrl+D / Ctrl+Z):")
        lines = []
        try:
            while True:
                line = input()
                if line.strip() == "EOF":
                    break
                lines.append(line)
        except EOFError:
            pass
        message_text = "\n".join(lines)
        
    if not message_text.strip():
        print("Текст сообщения пуст. Отмена.")
        sys.exit(1)
        
    print("\nВаше сообщение будет выглядеть так:")
    print("-" * 40)
    print(message_text)
    print("-" * 40)
    confirm = input("Отправить это сообщение всем пользователям? (y/n): ")
    
    if confirm.lower() == 'y':
        asyncio.run(broadcast_message(message_text))
    else:
        print("Отменено.")
