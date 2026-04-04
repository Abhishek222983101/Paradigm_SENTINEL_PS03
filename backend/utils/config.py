# ═══════════════════════════════════════════════════════════════════════════
# SENTINEL CONFIGURATION
# Financial Fraud Intelligence Platform - Backend Configuration
# ═══════════════════════════════════════════════════════════════════════════

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses pydantic-settings for validation and type coercion.
    """
    
    # ─────────────────────────────────────────────────────────────────────────
    # Application Settings
    # ─────────────────────────────────────────────────────────────────────────
    APP_NAME: str = "SENTINEL"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Financial Fraud Intelligence Platform"
    DEBUG: bool = True
    
    # ─────────────────────────────────────────────────────────────────────────
    # Server Settings
    # ─────────────────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    
    # ─────────────────────────────────────────────────────────────────────────
    # CORS Settings
    # ─────────────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ]
    
    # ─────────────────────────────────────────────────────────────────────────
    # Database Settings
    # ─────────────────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./sentinel.db"
    REDIS_URL: str = "redis://localhost:6379"
    
    # ─────────────────────────────────────────────────────────────────────────
    # Mock Mode Toggle
    # When True, uses Faker-generated data instead of ML models
    # ─────────────────────────────────────────────────────────────────────────
    USE_MOCK_ML: bool = True
    
    # ─────────────────────────────────────────────────────────────────────────
    # WebSocket Settings
    # ─────────────────────────────────────────────────────────────────────────
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_TRANSACTION_RATE: float = 2.5  # Transactions per second in mock mode
    
    # ─────────────────────────────────────────────────────────────────────────
    # ML Model Settings (for when USE_MOCK_ML is False)
    # ─────────────────────────────────────────────────────────────────────────
    MODEL_PATH: str = "./models"
    FUSION_MODEL_PATH: Optional[str] = None
    TABULAR_MODEL_PATH: Optional[str] = None
    SEQUENCE_MODEL_PATH: Optional[str] = None
    GRAPH_MODEL_PATH: Optional[str] = None
    
    # ─────────────────────────────────────────────────────────────────────────
    # LLM Settings (Mistral for Investigation Reports)
    # ─────────────────────────────────────────────────────────────────────────
    MISTRAL_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    FEATHERLESS_API_KEY: Optional[str] = None
    FEATHERLESS_BASE_URL: str = "https://api.featherless.ai/v1"
    
    # ─────────────────────────────────────────────────────────────────────────
    # Experiment Tracking
    # ─────────────────────────────────────────────────────────────────────────
    WANDB_API_KEY: Optional[str] = None
    WANDB_PROJECT: str = "sentinel-fraud"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance.
    Returns the same Settings object for all calls.
    """
    return Settings()


# Export a global settings instance for convenience
settings = get_settings()
