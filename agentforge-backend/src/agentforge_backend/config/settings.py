from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_VERSION: str = "1.0.0"

    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Database - Supabase PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT settings
    JWT_SECRET: str = "change_this_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_REFRESH_TOKEN_ROTATION: bool = True

    # Legacy settings (for backward compatibility)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CORS_ORIGINS: str = '["http://localhost:3000","http://localhost:8000","http://localhost:5173","http://127.0.0.1:5173"]'
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = '["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]'
    CORS_ALLOW_HEADERS: str = '["*"]'
    CORS_EXPOSE_HEADERS: str = '["*"]'
    CORS_MAX_AGE: int = 600

    # Security
    SECURITY_HEADERS_ENABLED: bool = True
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"
    RATE_LIMIT_REFRESH: str = "10/minute"
    RATE_LIMIT_AI: str = "20/minute"
    RATE_LIMIT_UPLOAD: str = "10/minute"
    RATE_LIMIT_DEFAULT: str = "100/minute"

    # File upload
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_FILE_TYPES: str = '["image/jpeg", "image/png", "image/gif", "application/pdf", "text/plain"]'

    AGENTS_SERVICE_URL: str = "http://host.docker.internal:8001"
    AI_SERVICES_URL: str = "http://agentforge-ai-services:8000"
    INTEGRATIONS_SERVICE_URL: str = "http://agentforge-integrations:8000"

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # Monitoring
    METRICS_ENABLED: bool = True
    METRICS_PATH: str = "/metrics"

    # Logging
    STRUCTURED_LOGGING: bool = True
    LOG_SENSITIVE_FIELDS: str = '["password", "token", "secret", "authorization", "cookie", "api_key", "refresh_token"]'

    # Supabase Storage Buckets
    STORAGE_BUCKET_AGENT_ASSETS: str = "agent-assets"
    STORAGE_BUCKET_WORKSPACE_FILES: str = "workspace-files"
    STORAGE_BUCKET_AVATARS: str = "avatars"
    STORAGE_BUCKET_DOCUMENTS: str = "documents"

    # Backend URL for webhooks
    BACKEND_URL: str = "http://localhost:8000"

    @property
    def cors_origins_list(self) -> List[str]:
        origins = json.loads(self.CORS_ORIGINS)
        # Normalize: strip trailing slashes for consistent matching
        normalized = [origin.rstrip("/") for origin in origins]
        # Also include versions with trailing slash to handle browser variations
        result = []
        for origin in normalized:
            result.append(origin)
            result.append(origin + "/")
        return result

    @property
    def cors_allow_methods_list(self) -> List[str]:
        return json.loads(self.CORS_ALLOW_METHODS)

    @property
    def cors_allow_headers_list(self) -> List[str]:
        return json.loads(self.CORS_ALLOW_HEADERS)

    @property
    def allowed_file_types_list(self) -> List[str]:
        return json.loads(self.ALLOWED_FILE_TYPES)

    @property
    def log_sensitive_fields_list(self) -> List[str]:
        return json.loads(self.LOG_SENSITIVE_FIELDS)


settings = Settings()