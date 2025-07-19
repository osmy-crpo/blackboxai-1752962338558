from pydantic_settings import BaseSettings
from typing import List, Optional
from decouple import config
import os

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Warehouse Management System"
    VERSION: str = "1.0.0"
    DEBUG: bool = config("DEBUG", default=False, cast=bool)
    
    # Database Settings
    DATABASE_URL: str = config(
        "DATABASE_URL", 
        default="postgresql+asyncpg://warehouse_user:warehouse_pass@localhost:5432/warehouse_db"
    )
    
    # Security Settings
    SECRET_KEY: str = config("SECRET_KEY", default="your-super-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int)
    REFRESH_TOKEN_EXPIRE_DAYS: int = config("REFRESH_TOKEN_EXPIRE_DAYS", default=7, cast=int)
    
    # CORS Settings
    ALLOWED_HOSTS: List[str] = config(
        "ALLOWED_HOSTS", 
        default="http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000",
        cast=lambda v: [s.strip() for s in v.split(',')]
    )
    
    # IP Whitelisting
    ENABLE_IP_WHITELIST: bool = config("ENABLE_IP_WHITELIST", default=False, cast=bool)
    WHITELISTED_IPS: List[str] = config(
        "WHITELISTED_IPS",
        default="127.0.0.1,::1,localhost",
        cast=lambda v: [s.strip() for s in v.split(',')]
    )
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = config("RATE_LIMIT_PER_MINUTE", default=60, cast=int)
    
    # Redis Settings (for caching and sessions)
    REDIS_URL: str = config("REDIS_URL", default="redis://localhost:6379/0")
    
    # Email Settings (for notifications)
    SMTP_HOST: str = config("SMTP_HOST", default="")
    SMTP_PORT: int = config("SMTP_PORT", default=587, cast=int)
    SMTP_USERNAME: str = config("SMTP_USERNAME", default="")
    SMTP_PASSWORD: str = config("SMTP_PASSWORD", default="")
    SMTP_USE_TLS: bool = config("SMTP_USE_TLS", default=True, cast=bool)
    
    # File Upload Settings
    MAX_FILE_SIZE: int = config("MAX_FILE_SIZE", default=10485760, cast=int)  # 10MB
    UPLOAD_DIR: str = config("UPLOAD_DIR", default="uploads")
    
    # Pagination Settings
    DEFAULT_PAGE_SIZE: int = config("DEFAULT_PAGE_SIZE", default=20, cast=int)
    MAX_PAGE_SIZE: int = config("MAX_PAGE_SIZE", default=100, cast=int)
    
    # Backup Settings
    BACKUP_DIR: str = config("BACKUP_DIR", default="backups")
    AUTO_BACKUP_ENABLED: bool = config("AUTO_BACKUP_ENABLED", default=True, cast=bool)
    BACKUP_RETENTION_DAYS: int = config("BACKUP_RETENTION_DAYS", default=30, cast=int)
    
    # Logging Settings
    LOG_LEVEL: str = config("LOG_LEVEL", default="INFO")
    LOG_FILE: str = config("LOG_FILE", default="logs/warehouse.log")
    
    # 2FA Settings
    ENABLE_2FA: bool = config("ENABLE_2FA", default=False, cast=bool)
    TOTP_ISSUER: str = config("TOTP_ISSUER", default="Warehouse Management System")
    
    # WebSocket Settings
    ENABLE_WEBSOCKET: bool = config("ENABLE_WEBSOCKET", default=True, cast=bool)
    
    # Internationalization
    DEFAULT_LANGUAGE: str = config("DEFAULT_LANGUAGE", default="en")
    SUPPORTED_LANGUAGES: List[str] = config(
        "SUPPORTED_LANGUAGES",
        default="en,fr,ar",
        cast=lambda v: [s.strip() for s in v.split(',')]
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.BACKUP_DIR, exist_ok=True)
os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
