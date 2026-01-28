import os
import pytest
try:
    from backend.config import get_settings, DevelopmentSettings, ProductionSettings
except ImportError:
    from config import get_settings, DevelopmentSettings, ProductionSettings

def test_development_config():
    """Verify development settings are loaded by default."""
    os.environ["APP_ENV"] = "development"
    get_settings.cache_clear() # Clear lru_cache
    settings = get_settings()
    assert isinstance(settings, DevelopmentSettings)
    assert settings.DEBUG is True
    assert "http://localhost:3000" in settings.CORS_ORIGINS

def test_production_config():
    """Verify production settings are loaded when env var is set."""
    os.environ["APP_ENV"] = "production"
    os.environ["FRONTEND_URL"] = "https://prod.example.com"
    get_settings.cache_clear()
    settings = get_settings()
    assert isinstance(settings, ProductionSettings)
    assert settings.DEBUG is False
    assert "https://prod.example.com" in settings.CORS_ORIGINS

def test_production_default_cors():
    """Verify CORS handles missing frontend url gracefully or logic holds."""
    os.environ["APP_ENV"] = "production"
    if "FRONTEND_URL" in os.environ:
        del os.environ["FRONTEND_URL"]
    
    get_settings.cache_clear()
    settings = get_settings()
    # Should default to empty list or None if not set, depending on logic
    # In our code: cors_origins_list returns [] if None
    assert settings.CORS_ORIGINS == [] 
