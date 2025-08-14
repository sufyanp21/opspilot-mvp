import os
from typing import Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/opspilot"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Application
    APP_ENV: str = "dev"
    FILE_STORAGE_DIR: str = "/data/uploads"
    
    # AI/ML
    AI_ENABLED: bool = False
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Performance
    MAX_WORKERS: int = 4
    BATCH_SIZE: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
