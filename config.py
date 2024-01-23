from pydantic_settings import BaseSettings


class Config(BaseSettings):
    ACCOUNT_ID: str
    REGION: str
