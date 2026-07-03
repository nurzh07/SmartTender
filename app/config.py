from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Email (SMTP)
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@smarttender.kz"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""

    # Goszakupki.kz
    GOSZAKUPKI_API_URL: str = "https://goszakupki.kz/api/v1"
    GOSZAKUPKI_API_KEY: str = ""
    GOSZAKUPKI_TIMEOUT: float = 5.0
    GOSZAKUPKI_MAX_RETRIES: int = 3

    # BIN verification (stat.gov.kz)
    EGOV_API_URL: str = "https://stat.gov.kz/api/legal/rest/names/bin"
    EGOV_API_TIMEOUT: float = 5.0

    # Stripe payments
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""

    # Odoo ERP
    ODOO_URL: str = "http://localhost:8069"
    ODOO_DB: str = "smarttender"
    ODOO_USERNAME: str = "admin"
    ODOO_PASSWORD: str = ""
    ODOO_TIMEOUT: float = 10.0
    ODOO_MAX_RETRIES: int = 3

    # File storage
    UPLOAD_DIR: str = "uploads"
    USE_MINIO: bool = False
    MINIO_ENDPOINT: str = "smarttender_minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "smarttender-reports"
    MINIO_SECURE: bool = False

    APP_PUBLIC_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
