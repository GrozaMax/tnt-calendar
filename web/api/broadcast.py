"""
API для рассылки сообщений
"""
import logging
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from telegram import Bot
from telegram.error import TelegramError

from src.database.connection import get_session
from src.models import User
from src.config import Config
from web.api.auth import require_admin

router = APIRouter()
logger = logging.getLogger(__name__)

class BroadcastRequest(BaseModel):
    message: str
    target_users: Optional[List[int]] = None  # List of user IDs. If None, send to all

@router.post("/")
async def send_broadcast(
    data: BroadcastRequest,
    admin: User = Depends(require_admin)
):
    if not data.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    bot = Bot(Config.BOT_TOKEN)

    if data.target_users:
        query = select(User).where(User.id.in_(data.target_users))
    else:
        query = select(User)

    async with get_session() as session:
        result = await session.execute(query)
        users = result.scalars().all()

    if not users:
        raise HTTPException(status_code=404, detail="No users found to send message to")

    success_count = 0
    fail_count = 0

    # Отправляем сообщения (с задержкой, чтобы не превысить лимиты Telegram ~30 msg/s)
    for user in users:
        if not user.telegram_id:
            continue

        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=data.message,
                parse_mode="Markdown"
            )
            success_count += 1
            await asyncio.sleep(0.05)
        except TelegramError as e:
            logger.warning(f"Failed to send broadcast to {user.telegram_id}: {e}")
            fail_count += 1

    return {
        "success": True,
        "sent": success_count,
        "failed": fail_count,
        "total": len(users)
    }
