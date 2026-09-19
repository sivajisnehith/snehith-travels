import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Snehith Travels API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgrespassword@localhost:5432/snehith_travels"
    SQLITE_FALLBACK_URL: str = "sqlite:///./snehith_travels.db"
    
    # Security
    SECRET_KEY: str = "snehith_super_secret_hackathon_jwt_key_2026_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Seat Hold Duration
    SEAT_HOLD_DURATION_MINUTES: int = 10

    # Razorpay Test Mode Configuration
    RAZORPAY_KEY_ID: str = "rzp_test_placeholder"
    RAZORPAY_KEY_SECRET: str = "placeholder_secret"
    RAZORPAY_WEBHOOK_SECRET: str = "placeholder_webhook_secret"
    FRONTEND_URL: str = "http://localhost:3000"

    # Meta WhatsApp Cloud API
    WHATSAPP_API_TOKEN: Optional[str] = "EAAPO0LpiQ4cBSomoErVw8nFrWK5J6pFnahMg5bryofI0cDZA6zH8gZCvUMF14PPq6bDRGRa4dTMZCQIWgiAGanwh94GEnTH0Dm3RrzXVEo6vEdr2oImfWWH0gmJQgjGpp7cKpaqobV6AZBEjMz4ZBm8h3c4a0KeecXe8nWFg2fxZBWxPZAi61HfxUsHG5OqIR9cogZDZD"
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = "1341186229071206"
    WHATSAPP_API_VERSION: str = "v22.0"
    # Must match an approved Meta WhatsApp template for Snehith Travels.
    WHATSAPP_PAYMENT_TEMPLATE_NAME: str = "snehith_travels_payment_link"
    WHATSAPP_PAYMENT_TEMPLATE_LANG: str = "en"
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
