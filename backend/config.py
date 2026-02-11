from functools import lru_cache
from typing import List
from urllib.parse import quote_plus

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Settings(BaseSettings):
    """
    Loads env variables from .env file.
    Also allows to define default values for configs
    """

    # class Config:
    #     env_file=".env"
    #     env_file_encoding = "utf-8"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    project_name: str = "Task Management System"
    environment: str = "local"
    super_admin_email: str = "a@b.c"
    super_admin_password: str = "1234"
    super_admin_name: str = "abcd"
    super_admin_phone_number: str = 1234

    # Database
    db_user: str = "user"
    db_password: str = "1234"
    db_host: str = "host"
    db_port: int = 1234
    db_name: str = "task_management"
    database_url: str = ""

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_database_url(cls, database_url: str | List[str], info) -> str:
        if database_url:
            return database_url
        data = info.data
        password: str = quote_plus(data["db_password"])
        return f"postgresql+psycopg2://{data['db_user']}:{password}@{data['db_host']}:{data['db_port']}/{data['db_name']}"

    # Celery
    broker: str = "redis://localhost:6379/0"
    celery_backend_url: str = "db+" + database_url

    # Security
    allowed_origins: List[AnyHttpUrl] | List[str] = []

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def assemble_allowed_origins(cls, origins: str | List[str]) -> List[str]:
        if isinstance(origins, str):
            return [origin.strip() for origin in origins.split(",") if origin.split()]
        return origins

    secret_key: str = "SECRET_KEY"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


@lru_cache
def get_settings() -> Settings:
    """Return cached config"""
    return Settings()
