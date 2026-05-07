from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Bot Settings
    BOT_TOKEN: str
    ADMIN_IDS: list[int] = []
    
    # Database Settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./tokflare.db"
    REDIS_URL: Optional[str] = None
    
    # Payment Settings (NOWPayments example)
    NOWPAYMENTS_API_KEY: Optional[str] = None
    NOWPAYMENTS_IPN_SECRET: Optional[str] = None
    
    # SMM Panel Settings
    SMM_API_URL: Optional[str] = None
    SMM_API_KEY: Optional[str] = None
    
    # Business Logic
    MIN_COMMENTS: int = 10
    MAX_COMMENTS: int = 1000
    PROFIT_MARGIN: float = 1.5  # 50% profit margin
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
