from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    ENV_STATE: str | None = None
    model_config = SettingsConfigDict(
        env_file='env/.env',
        extra='ignore'
    )


class GlobalConfig(BaseConfig):
    DATABASE_POOL_SIZE: int
    DATABASE_MAX_OVERFLOW: int
    DATABASE_URL: str

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
