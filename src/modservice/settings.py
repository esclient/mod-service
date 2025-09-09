import logging
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict

from .infisical_client import create_infisical_manager


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str | None = "0.0.0.0"
    port: int | None = 7777
    database_url: str | None = None

    log_level: str | None = None
    log_format: str | None = None
    log_datefmt: str | None = None

    s3_api_endpoint: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_bucket_name: str | None = None
    s3_ssl_verify: bool | None = True

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        try:
            manager = create_infisical_manager()
            secrets = manager.get_secrets(
                [
                    "DATABASE_URL",
                    "LOG_LEVEL",
                    "LOG_FORMAT",
                    "LOG_DATEFMT",
                    "S3_API_ENDPOINT",
                    "S3_ACCESS_KEY",
                    "S3_SECRET_KEY",
                    "S3_BUCKET_NAME",
                    "S3_SSL_VERIFY",
                ]
            )
            self.database_url = secrets.get("DATABASE_URL", self.database_url)
            self.log_level = secrets.get("LOG_LEVEL", self.log_level)
            self.log_format = secrets.get("LOG_FORMAT", self.log_format)
            self.log_datefmt = secrets.get("LOG_DATEFMT", self.log_datefmt)
            self.s3_api_endpoint = secrets.get(
                "S3_API_ENDPOINT", self.s3_api_endpoint
            )
            self.s3_access_key = secrets.get(
                "S3_ACCESS_KEY", self.s3_access_key
            )
            self.s3_secret_key = secrets.get(
                "S3_SECRET_KEY", self.s3_secret_key
            )
            self.s3_bucket_name = secrets.get(
                "S3_BUCKET_NAME", self.s3_bucket_name
            )
            s3_verify_raw = secrets.get("S3_SSL_VERIFY", self.s3_ssl_verify)
            self.s3_ssl_verify = self._coerce_bool(s3_verify_raw)
        except Exception as e:
            logging.error(f"Infisical load failed: {e}")

    def configure_logging(self) -> None:
        level = self._coerce_log_level(self.log_level)
        fmt = (
            self.log_format
            or "%(asctime)s %(levelname)s %(name)s: %(message)s"
        )
        datefmt = self.log_datefmt or "%Y-%m-%d %H:%M:%S"
        logging.basicConfig(
            level=level, format=fmt, datefmt=datefmt, force=True
        )

    @staticmethod
    def _coerce_log_level(level: str | None) -> int:
        if level is None:
            return logging.INFO
        if isinstance(level, int):
            return level
        return logging._nameToLevel.get(
            str(level).strip().upper(), logging.INFO
        )

    @staticmethod
    def _coerce_bool(value: str | bool | None) -> bool | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off"}:
            return False
        return None
