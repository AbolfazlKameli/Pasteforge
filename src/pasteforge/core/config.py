from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


class BaseConfig(BaseSettings):
    ENV_STATE: str | None = None
    model_config = SettingsConfigDict(
        env_file='env/.env',
        extra='ignore'
    )


class GlobalConfig(BaseConfig):
    TIMEZONE: str

    UNUSABLE_PASSWORD_MARKER: str = "!UNUSABLE"

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
