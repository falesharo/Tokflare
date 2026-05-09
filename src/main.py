import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher

from src.core.config import settings
from src.core.logging import setup_logging
from src.database.db import init_db
from src.bot.handlers import start, order, history, admin, wallet
from src.bot.middlewares import DbSessionMiddleware, UserManagerMiddleware, LoggingMiddleware, RateLimitMiddleware
from src.bot.utils import router as error_router
from src.core.tasks import payment_verification_task
from src.core.smm.cache import service_cache

async def main():
    # Setup logging
    setup_logging()
    
    # Initialize Database & Cache
    await init_db()
    await service_cache.refresh_cache()
    
    # Initialize Storage
    if settings.REDIS_URL:
        from aiogram.fsm.storage.redis import RedisStorage
        from redis.asyncio import Redis
        redis = Redis.from_url(settings.REDIS_URL)
        storage = RedisStorage(redis)
    else:
        from aiogram.fsm.storage.memory import MemoryStorage
        storage = MemoryStorage()
    
    # Initialize Bot and Dispatcher
    bot = Bot(token=settings.BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(storage=storage)
    
    # Setup Middlewares
    dp.update.outer_middleware(LoggingMiddleware())
    dp.update.middleware(DbSessionMiddleware())
    dp.update.middleware(UserManagerMiddleware())
    dp.update.middleware(RateLimitMiddleware())
    
    # Register handlers
    dp.include_router(error_router)
    dp.include_router(start.router)
    dp.include_router(order.router)
    dp.include_router(wallet.router)
    dp.include_router(history.router)
    dp.include_router(admin.router)
    
    # Start background tasks
    asyncio.create_task(payment_verification_task(bot))
    
    # Start polling
    logging.info("TokFlare Bot started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
