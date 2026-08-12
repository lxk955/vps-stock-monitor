import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "VPS Stock & Price Monitor"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = "sqlite+aiosqlite:///./vps_stock.db"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "vps_panel_stock_secret_key_2026_super_safe")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123456")
    DEFAULT_CHECK_INTERVAL_SECONDS: int = 180
    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
