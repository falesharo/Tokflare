import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import User
from src.database.db import async_session
from src.core.config import settings
import time

logger = logging.getLogger(__name__)

class DbSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        async with async_session() as session:
            data["session"] = session
            return await handler(event, data)

class UserManagerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        tg_user: TelegramUser = data.get("event_from_user")
        if not tg_user:
            return await handler(event, data)

        session: AsyncSession = data["session"]
        user = await session.get(User, tg_user.id)
        
        if not user:
            user = User(
                id=tg_user.id,
                username=tg_user.username,
                full_name=tg_user.full_name
            )
            session.add(user)
            await session.commit()
            logger.info(f"New user registered: {tg_user.id}")
        
        data["user"] = user
        return await handler(event, data)

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self):
        self.user_requests = {}
        
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user: TelegramUser = data.get("event_from_user")
        if not user:
            return await handler(event, data)
        
        user_id = user.id
        current_time = time.time()
        
        # Initialize or clean up old requests
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        
        # Remove requests older than 1 minute
        self.user_requests[user_id] = [t for t in self.user_requests[user_id] if current_time - t < 60]
        
        # Check rate limit
        if len(self.user_requests[user_id]) >= settings.RATE_LIMIT:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            if hasattr(event, 'message'):
                await event.message.answer("⚠️ <b>Too Many Requests</b>\nPlease slow down and try again in a minute.")
            return None
        
        # Add current request
        self.user_requests[user_id].append(current_time)
        
        return await handler(event, data)

class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Log every incoming update
        user: TelegramUser = data.get("event_from_user")
        user_id = user.id if user else "Unknown"
        logger.info(f"Received update from user {user_id}")
        return await handler(event, data)
