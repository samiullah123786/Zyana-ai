"""Configuration management for Zyana backend."""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Fal AI
    fal_api_key: str = Field(..., alias="FAL_API_KEY")
    
    # Telegram
    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")
    
    # Google OAuth
    google_client_id: str = Field(..., alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(..., alias="GOOGLE_CLIENT_SECRET")
    google_project_id: str = Field(..., alias="GOOGLE_PROJECT_ID")
    google_redirect_uri: str = Field(
        default="http://localhost:8000/auth/google/callback",
        alias="GOOGLE_REDIRECT_URI"
    )
    
    # Supabase
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_anon_key: str = Field(..., alias="SUPABASE_ANON_KEY")
    supabase_service_key: str = Field(..., alias="SUPABASE_SERVICE_KEY")
    
    # Qdrant
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(default=None, alias="QDRANT_API_KEY")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    
    # PostgreSQL
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="zyana_dev", alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="example", alias="POSTGRES_PASSWORD")
    postgres_conn: Optional[str] = Field(default=None, alias="POSTGRES_CONN")
    
    # Backend
    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    webhook_url: Optional[str] = Field(default=None, alias="WEBHOOK_URL")
    
    # Environment
    environment: str = Field(default="development", alias="ENVIRONMENT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    @property
    def postgres_connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        if self.postgres_conn:
            return self.postgres_conn
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


# Global settings instance
settings = Settings()

