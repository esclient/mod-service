import logging

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    host: str = Field(validation_alias="HOST")
    port: int = Field(validation_alias="PORT")
    database_url: str = Field(validation_alias="DATABASE_URL")

    log_level: str = Field(validation_alias="LOG_LEVEL")
    log_format: str = Field(validation_alias="LOG_FORMAT")
    log_datefmt: str = Field(validation_alias="LOG_DATEFMT")

    s3_api_endpoint: str = Field(validation_alias="S3_API_ENDPOINT")
    s3_access_key: str = Field(validation_alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(validation_alias="S3_SECRET_KEY")
    s3_bucket_name: str = Field(validation_alias="S3_BUCKET_NAME")
    s3_ssl_verify: bool = Field(
        validation_alias="S3_SSL_VERIFY"
    )  # TODO: добавить поддержку сертификатов, иначе без защищённого подключения упиздят все моды

    def configure_logging(self) -> None:
        logging.basicConfig(
            level=self.log_level,
            format=self.log_format,
            datefmt=self.log_datefmt,
        )
