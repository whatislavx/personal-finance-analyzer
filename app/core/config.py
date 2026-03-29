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

    class Config:
        env_file = ".env"


settings = Settings()
