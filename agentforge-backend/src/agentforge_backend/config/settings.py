from pydantic_settings import BaseSettings
from typing import List
import json

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "postgresql+asyncpg://backend:backendpass@localhost:5432/agentforge"
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET: str = "change_this_in_production"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CORS_ORIGINS: str = '["http://localhost:3000","http://localhost:8000"]'

    AGENTS_SERVICE_URL: str = "http://agentforge-agents:8000"
    AI_SERVICES_URL: str = "http://agentforge-ai-services:8000"
    INTEGRATIONS_SERVICE_URL: str = "http://agentforge-integrations:8000"

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()