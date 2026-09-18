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
    WHATSAPP_API_TOKEN: Optional[str] = "EAAPO0LpiQ4cBSnq6ykrNlq9DlC5Jvz22hTGBwfK5KHpTrJ90w5cxCJwlOZBGes2kz5NZCZAprrch51SOOhfOffZATxzn2ug3dR8JM3EhiK6JIvPPnMKTo4rxi80o83oted0k1Xnk8SolQ8XOTNqlBLlmxqhPoumzHFz9nOoFJRI7mFs7ZB4MXvIHejW9fxFqy9S3cru1AoEsd3F97KZAdLDN5d2ro6tM32S4wAATY5WZClS0s6p8fxZBdKkuWEa5fzEsSVZBFXtMtxXR57ZBo68Sv3gnzAHgZDZD"
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = "1341186229071206"
    WHATSAPP_API_VERSION: str = "v22.0"
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
