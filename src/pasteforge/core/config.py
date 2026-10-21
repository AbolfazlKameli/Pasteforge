from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


class BaseConfig(BaseSettings):
    ENV_STATE: str | None = None
    model_config = SettingsConfigDict(
        env_file='env/.env',
        extra='ignore'
    )


class OTPSettings(BaseModel):
    EXPIRATION_TIME: timedelta = timedelta(minutes=2)
    MAX_ATTEMPTS: int = Field(default=3, ge=1)
    BLACKLIST_EXPIRATION_TIME_LEVELS: list[str] = ["1", "2", "3"]
    BLACKLIST_EXPIRATION_TIME: dict[str, timedelta] = {
        "1": timedelta(minutes=5),
        "2": timedelta(minutes=10),
        "3": timedelta(minutes=20),
    }


class GlobalConfig(BaseConfig):
    TIMEZONE: str
    SECRET_KEY: str

    UNUSABLE_PASSWORD_MARKER: str = "!UNUSABLE"

    OTP_SETTINGS: OTPSettings = OTPSettings()

    LOG_LEVEL: LogLevel = 'DEBUG'
    SQLALCHEMY_LOG_LEVEL: LogLevel = 'DEBUG'
    LOG_DIR: Path = Path('logs')
    LOG_MAX_BYTES: int = 10_000_000
    LOG_BACKUP_COUNT: int = 5

    DATABASE_POOL_SIZE: int
    DATABASE_MAX_OVERFLOW: int
    DATABASE_URL: str

    EMAIL_HOSTNAME: str
    EMAIL_PORT: int
    EMAIL_USE_TLS: bool
    EMAIL_HOST_USERNAME: str
    EMAIL_HOST_PASSWORD: str

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    DEBUG: bool = False


class DevConfig(GlobalConfig):
    DEBUG: bool = True
    model_config = SettingsConfigDict(env_file='env/.dev.env', env_prefix='DEV_')


class TestConfig(GlobalConfig):
    DEBUG: bool = True

    model_config = SettingsConfigDict(env_file='env/.test.env', env_prefix='TEST_')


class ProdConfig(GlobalConfig):
    DEBUG: bool = False
    model_config = SettingsConfigDict(env_file='env/.prod.env', env_prefix='PROD_')


@lru_cache()
def get_configs(state: str | None) -> GlobalConfig:
    if state is None:
        return DevConfig(ENV_STATE='development')

    match state.casefold():
        case 'production' | 'prod':
            return ProdConfig(ENV_STATE='production')
        case 'development' | 'dev':
            return DevConfig(ENV_STATE='development')
        case 'test':
            return TestConfig(ENV_STATE='test')
        case _:
            return DevConfig(ENV_STATE='development')


configs = get_configs(BaseConfig().ENV_STATE)
