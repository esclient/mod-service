from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = Field("0.0.0.0", env = "HOST")
    port: int = Field(50051, env = "PORT")

    database_url: str = Field (..., env="DATABASE_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()