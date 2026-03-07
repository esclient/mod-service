import logging

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
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
    s3_verify: bool = Field(validation_alias="S3_VERIFY")

    kafka_brokers: str = Field(
        validation_alias="KAFKA_BROKERS"
    )
    kafka_request_topic: str = Field(
        validation_alias="KAFKA_REQUEST_TOPIC"
    )
    kafka_result_topic: str = Field(
        validation_alias="KAFKA_RESULT_TOPIC"
    )
    kafka_consumer_group_id: str = Field(
        validation_alias="KAFKA_CONSUMER_GROUP_ID"
    )

    @field_validator(
        "kafka_brokers",
        "kafka_request_topic",
        "kafka_result_topic",
        "kafka_consumer_group_id",
    )
    @classmethod
    def validate_non_empty_string(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError(
                "Kafka configuration fields must be non-empty strings"
            )
        return v

    def configure_logging(self) -> None:
        logging.basicConfig(
            level=self.log_level,
            format=self.log_format,
            datefmt=self.log_datefmt,
        )
