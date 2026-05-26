from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    DB_USER: str = Field(default="")
    DB_PASSWORD: str = Field(default="")
    DB_HOST: str = Field(default="localhost")
    DB_NAME: str = Field(default="")
    DB_PORT: int = Field(default=5432)

    RABBITMQ_URL: str = Field(default="amqp://guest:guest@localhost/")
    RABBITMQ_EXCHANGE: str = "jobs"

    JWT_SECRET_KEY: str = Field(default="dev-secret-key-keep-it-short")
    JWT_ALGORITHM: str = "HS256"

    S3_BUCKET: str = "results"
    S3_REGION: str = Field(default="eu-central-1")
    S3_KEY_PREFIX: str = Field(default="results")

    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None)
    AWS_SESSION_TOKEN: Optional[str] = Field(default=None)

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
