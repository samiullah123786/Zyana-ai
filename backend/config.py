"""Configuration management for Zyana backend."""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Fal AI (Legacy - Optional for future use)
    fal_api_key: Optional[str] = Field(default=None, alias="FAL_API_KEY")
    
    # Groq AI (Whisper Transcription)
    groq_api_key: str = Field(..., alias="GROQ_API_KEY")
    groq_transcribe_model: str = Field(
        default="whisper-large-v3-turbo",
        alias="GROQ_TRANSCRIBE_MODEL"
    )
    max_chunk_seconds: int = Field(default=180, alias="MAX_CHUNK_SECONDS")
    whisper_local_enabled: bool = Field(default=False, alias="WHISPER_LOCAL_ENABLED")
    voice_storage_provider: str = Field(
        default="supabase",
        alias="VOICE_STORAGE_PROVIDER"
    )  # Options: "supabase", "s3", "local"
    
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
    google_credentials_path: Optional[str] = Field(default=None, alias="GOOGLE_CREDENTIALS_PATH")
    google_token_path: Optional[str] = Field(default=None, alias="GOOGLE_TOKEN_PATH")
    google_sheets_folder_id: Optional[str] = Field(default=None, alias="GOOGLE_SHEETS_FOLDER_ID")
    
    # Supabase
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_anon_key: str = Field(..., alias="SUPABASE_ANON_KEY")
    supabase_service_key: str = Field(..., alias="SUPABASE_SERVICE_KEY")
    
    # Qdrant
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(default=None, alias="QDRANT_API_KEY")
    
    # Redis
    redis_url: str = Field(
        default="redis://default:MNI6xU3YrFLdSlkyngCHy9HYt3al7F3h@redis-13891.c270.us-east-1-3.ec2.redns.redis-cloud.com:13891",
        alias="REDIS_URL"
    )
    upstash_redis_rest_token: Optional[str] = Field(default=None, alias="UPSTASH_REDIS_REST_TOKEN")
    
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
    
    # Calendar Intelligence
    default_timezone: str = Field(default="Asia/Karachi", alias="DEFAULT_TIMEZONE")
    confidence_threshold: float = Field(default=0.7, alias="CONFIDENCE_THRESHOLD")
    redis_session_ttl: int = Field(default=604800, alias="REDIS_SESSION_TTL")  # 7 days
    owner_name: str = Field(default="Sami", alias="OWNER_NAME")
    
    # CORS Settings
    frontend_url: Optional[str] = Field(default=None, alias="FRONTEND_URL")
    cors_origins: Optional[str] = Field(default=None, alias="CORS_ORIGINS")  # Comma-separated list
    
    # Memory & Learning Pipeline
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")  # Primary chat model
    embedding_provider: str = Field(default="openai", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    mirror_embed_k: int = Field(default=5, alias="MIRROR_EMBED_K")
    memory_summary_days: int = Field(default=90, alias="MEMORY_SUMMARY_DAYS")
    
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
    
    @property
    def backend_url(self) -> str:
        """Get backend URL based on environment."""
        if self.webhook_url:
            # If webhook URL is set, derive backend URL from it
            return self.webhook_url.replace("/webhook/telegram", "")
        elif self.is_production:
            return "https://zyana-backend.onrender.com"
        else:
            return f"http://{self.backend_host}:{self.backend_port}"


# Global settings instance
settings = Settings()

