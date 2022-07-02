from functools import lru_cache
from pydantic import BaseSettings


class Config(BaseSettings):
    ACCESS_TOKEN_EXPIRATION: int = 24 * 60 * 60
    REFRESH_TOKEN_EXPIRATION: int = 1 * 24 * 60 * 60

    PRIVATE_KEY: str
    PUBLIC_KEY: str
    REFRESH_PRIVATE_KEY: str

    DB: str
    DB_POOL_PRE_PING: bool = True
    DB_POOL_SIZE: int = 20
    DB_POOL_RECYCLE: int = 1800
    DB_ECHO: bool = False

    class Config:
        env_file = '.env'


@lru_cache
def get_config():
    return Config()


config = get_config()
