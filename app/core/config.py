from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_NAME: str
    DB_PORT: int

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost/"
    RABBITMQ_EXCHANGE: str = "jobs"

    # JWT
    JWT_SECRET_KEY: str = "change-me-to-a-secure-random-value"
    JWT_ALGORITHM: str = "HS256"

    # MinIO / S3
    S3_ENDPOINT: str = "localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "results"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"


settings = Settings()
