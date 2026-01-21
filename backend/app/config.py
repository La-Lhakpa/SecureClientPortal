from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import AnyUrl, Field


class Settings(BaseSettings):
    app_name: str = Field("Secure File Sharing Portal", alias="APP_NAME")
    env: str = Field("local", alias="ENV")
    database_url: str = Field("sqlite:///./app.db", alias="DATABASE_URL")
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    jwt_expires_minutes: int = Field(60, alias="JWT_EXPIRES_MINUTES")
    allowed_origins: str = Field("http://localhost:5173", alias="ALLOWED_ORIGINS")
    audit_log_to_file: bool = Field(True, alias="AUDIT_LOG_TO_FILE")
    audit_log_file: str = Field("logs/audit.log", alias="AUDIT_LOG_FILE")

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
