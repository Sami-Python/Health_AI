import os
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Base configuration with defaults common to all environments.
    """
    APP_ENV: str = "development"
    APP_NAME: str = "Health AI Coach"
    VERSION: str = "1.0.0"
    
    # Secrets / Keys (Prefer reading from env vars or Secret Manager)
    # Pydantic Settings will automatically read from env vars (case-insensitive)
    ENCRYPTION_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    
    # Paths
    DB_FILE_PATH: str = "/data/health_ai.db"
    
    # Firebase
    FIREBASE_PROJECT_ID: str = "personal-ai-coach-92c39"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None

    # CORS Defaults (Restrictive by default)
    CORS_ORIGINS: List[str] = []

    # Features
    DEBUG: bool = False
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )

class DevelopmentSettings(Settings):
    """
    Development environment settings.
    """
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]

class ProductionSettings(Settings):
    """
    Production environment settings.
    """
    DEBUG: bool = False
    # In production, we expect FRONTEND_URL to be set, or we default to a specific domain
    FRONTEND_URL: Optional[str] = None
    
    CORS_ORIGINS: List[str] = [
        "https://app.personalaicoach.ai",
        "https://www.personalaicoach.ai"
    ]
    
    @property
    def cors_origins_list(self) -> List[str]:
        # This property is kept for reference but CORS_ORIGINS above is what Pydantic uses
        origins = self.CORS_ORIGINS.copy()
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
             origins.append(self.FRONTEND_URL)
        return origins

    # Override Pydantic Validator if we want dynamic CORS_ORIGINS based on FRONTEND_URL
    # For simplicity, we'll assign it in the factory or use the property logic in main.py
    

class StagingSettings(Settings):
    """
    Staging environment settings.
    """
    DEBUG: bool = True
    FRONTEND_URL: Optional[str] = None

@lru_cache()
def get_settings() -> Settings:
    """
    Factory function to return the correct settings object based on APP_ENV.
    """
    # Read raw env var to decide which class to instantiate
    env = os.getenv("APP_ENV", "development").lower()
    
    if env == "production":
        settings = ProductionSettings()
        # Ensure CORS_ORIGINS is populated from FRONTEND_URL if not explicitly set
        if not settings.CORS_ORIGINS and settings.FRONTEND_URL:
            settings.CORS_ORIGINS = [settings.FRONTEND_URL]
        return settings
    
    elif env == "staging":
        return StagingSettings()
        
    return DevelopmentSettings()
