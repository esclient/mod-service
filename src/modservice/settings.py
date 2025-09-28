import logging
import os
from typing import Any

from dotenv import load_dotenv
from infisical_sdk import InfisicalSDKClient  # type: ignore[import-untyped]
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = ".env"

REQUIRED_ENV_VARS = [
    "HOST",
    "PORT",
    "INFISICAL_SERVER_TOKEN",
    "INFISICAL_PROJECT_ID",
    "INFISICAL_HOST",
    "INFISICAL_ENVIRONMENT",
    "INFISICAL_SECRET_PATH",
]

SECRETS = [
    "DATABASE_URL",
    "LOG_DATEFMT",
    "LOG_FORMAT",
    "LOG_LEVEL",
    "S3_ACCESS_KEY",
    "S3_API_ENDPOINT",
    "S3_BUCKET_NAME",
    "S3_SECRET_KEY",
    "S3_SSL_VERIFY",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str
    port: int
    database_url: str
    log_level: str
    log_format: str
    log_datefmt: str
    s3_api_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket_name: str
    s3_verify: bool

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv(ENV_FILE)
        missing_env = [
            name for name in REQUIRED_ENV_VARS if not os.environ.get(name)
        ]
        if missing_env:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_env)}"
            )

        secrets = cls._load_secrets(
            host=os.environ["INFISICAL_HOST"],
            server_token=os.environ["INFISICAL_SERVER_TOKEN"],
            project_id=os.environ["INFISICAL_PROJECT_ID"],
            environment_slug=os.environ["INFISICAL_ENVIRONMENT"],
            secret_path=os.environ["INFISICAL_SECRET_PATH"],
            secret_names=SECRETS,
        )

        return cls(
            host=os.environ["HOST"],
            port=os.environ["PORT"],
            database_url=secrets["DATABASE_URL"],
            s3_api_endpoint=secrets["S3_API_ENDPOINT"],
            s3_access_key=secrets["S3_ACCESS_KEY"],
            s3_secret_key=secrets["S3_SECRET_KEY"],
            s3_bucket_name=secrets["S3_BUCKET_NAME"],
            log_level=secrets["LOG_LEVEL"],
            log_format=secrets["LOG_FORMAT"],
            log_datefmt=secrets["LOG_DATEFMT"],
            s3_verify=secrets["S3_SSL_VERIFY"],
        )

    @staticmethod
    def _load_secrets(
        host: str,
        server_token: str,
        project_id: str,
        environment_slug: str,
        secret_path: str,
        secret_names: list[str],
    ) -> dict[str, str]:
        client: Any = InfisicalSDKClient(host=host, token=server_token)

        results: dict[str, str] = {}
        for name in secret_names:
            try:
                secret = client.secrets.get_secret_by_name(
                    secret_name=name,
                    project_id=project_id,
                    environment_slug=environment_slug,
                    secret_path=secret_path,
                )

                results[name] = secret.secretValue
            except Exception as e:
                raise ValueError(
                    f"Infisical: failed to fetch secret '{name}': {e}"
                ) from e

        return results

    def configure_logging(self) -> None:
        logging.basicConfig(
            level=self.log_level,
            format=self.log_format,
            datefmt=self.log_datefmt,
        )
