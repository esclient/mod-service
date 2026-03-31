"""Property-based tests for Settings configuration validation.

**Feature: mod-kafka-moderation**
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from modservice.settings import Settings


class TestSettingsConfigurationValidation:
    """Property-based tests for Settings configuration validation.

    **Validates: Requirements 1.4**
    """

    @given(
        kafka_bootstrap_servers=st.one_of(
            st.just(""),
            st.just("   "),
            st.none(),
        ),
        kafka_moderation_request_topic=st.text(min_size=1, max_size=50),
        kafka_moderation_response_topic=st.text(min_size=1, max_size=50),
        kafka_consumer_group_id=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=100)
    def test_property_9_invalid_bootstrap_servers_raises_validation_error(
        self,
        kafka_bootstrap_servers: str | None,
        kafka_moderation_request_topic: str,
        kafka_moderation_response_topic: str,
        kafka_consumer_group_id: str,
    ) -> None:
        """Property 9: Settings with invalid Kafka config should fail validation.

        **Feature: mod-kafka-moderation, Property 9: For any Settings
        instance with invalid Kafka configuration, validation should fail**

        Test that empty or None bootstrap_servers raises validation error.
        """
        with pytest.raises((ValidationError, ValueError)):
            Settings(
                host="localhost",
                port=50051,
                database_url="postgresql://test",
                log_level="INFO",
                log_format="%(message)s",
                log_datefmt="%Y-%m-%d",
                s3_api_endpoint="http://localhost:9000",
                s3_access_key="test",
                s3_secret_key="test",
                s3_bucket_name="test",
                s3_verify=False,
                kafka_bootstrap_servers=kafka_bootstrap_servers,
                kafka_moderation_request_topic=kafka_moderation_request_topic,
                kafka_moderation_response_topic=kafka_moderation_response_topic,
                kafka_consumer_group_id=kafka_consumer_group_id,
            )

    @given(
        kafka_bootstrap_servers=st.text(min_size=1, max_size=50),
        kafka_moderation_request_topic=st.one_of(
            st.just(""),
            st.just("   "),
            st.none(),
        ),
        kafka_moderation_response_topic=st.text(min_size=1, max_size=50),
        kafka_consumer_group_id=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=100)
    def test_property_9_invalid_request_topic_raises_validation_error(
        self,
        kafka_bootstrap_servers: str,
        kafka_moderation_request_topic: str | None,
        kafka_moderation_response_topic: str,
        kafka_consumer_group_id: str,
    ) -> None:
        """Property 9: Settings with invalid Kafka config should fail validation.

        **Feature: mod-kafka-moderation, Property 9: For any Settings
        instance with invalid Kafka configuration, validation should fail**

        Test that empty or None request topic raises validation error.
        """
        with pytest.raises((ValidationError, ValueError)):
            Settings(
                host="localhost",
                port=50051,
                database_url="postgresql://test",
                log_level="INFO",
                log_format="%(message)s",
                log_datefmt="%Y-%m-%d",
                s3_api_endpoint="http://localhost:9000",
                s3_access_key="test",
                s3_secret_key="test",
                s3_bucket_name="test",
                s3_verify=False,
                kafka_bootstrap_servers=kafka_bootstrap_servers,
                kafka_moderation_request_topic=kafka_moderation_request_topic,
                kafka_moderation_response_topic=kafka_moderation_response_topic,
                kafka_consumer_group_id=kafka_consumer_group_id,
            )

    @given(
        kafka_bootstrap_servers=st.text(min_size=1, max_size=50),
        kafka_moderation_request_topic=st.text(min_size=1, max_size=50),
        kafka_moderation_response_topic=st.one_of(
            st.just(""),
            st.just("   "),
            st.none(),
        ),
        kafka_consumer_group_id=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=100)
    def test_property_9_invalid_response_topic_raises_validation_error(
        self,
        kafka_bootstrap_servers: str,
        kafka_moderation_request_topic: str,
        kafka_moderation_response_topic: str | None,
        kafka_consumer_group_id: str,
    ) -> None:
        """Property 9: Settings with invalid Kafka config should fail validation.

        **Feature: mod-kafka-moderation, Property 9: For any Settings
        instance with invalid Kafka configuration, validation should fail**

        Test that empty or None response topic raises validation error.
        """
        with pytest.raises((ValidationError, ValueError)):
            Settings(
                host="localhost",
                port=50051,
                database_url="postgresql://test",
                log_level="INFO",
                log_format="%(message)s",
                log_datefmt="%Y-%m-%d",
                s3_api_endpoint="http://localhost:9000",
                s3_access_key="test",
                s3_secret_key="test",
                s3_bucket_name="test",
                s3_verify=False,
                kafka_bootstrap_servers=kafka_bootstrap_servers,
                kafka_moderation_request_topic=kafka_moderation_request_topic,
                kafka_moderation_response_topic=kafka_moderation_response_topic,
                kafka_consumer_group_id=kafka_consumer_group_id,
            )

    @given(
        kafka_bootstrap_servers=st.text(min_size=1, max_size=50),
        kafka_moderation_request_topic=st.text(min_size=1, max_size=50),
        kafka_moderation_response_topic=st.text(min_size=1, max_size=50),
        kafka_consumer_group_id=st.one_of(
            st.just(""),
            st.just("   "),
            st.none(),
        ),
    )
    @settings(max_examples=100)
    def test_property_9_invalid_consumer_group_id_raises_validation_error(
        self,
        kafka_bootstrap_servers: str,
        kafka_moderation_request_topic: str,
        kafka_moderation_response_topic: str,
        kafka_consumer_group_id: str | None,
    ) -> None:
        """Property 9: Settings with invalid Kafka config should fail validation.

        **Feature: mod-kafka-moderation, Property 9: For any Settings
        instance with invalid Kafka configuration, validation should fail**

        Test that empty or None consumer group ID raises validation error.
        """
        with pytest.raises((ValidationError, ValueError)):
            Settings(
                host="localhost",
                port=50051,
                database_url="postgresql://test",
                log_level="INFO",
                log_format="%(message)s",
                log_datefmt="%Y-%m-%d",
                s3_api_endpoint="http://localhost:9000",
                s3_access_key="test",
                s3_secret_key="test",
                s3_bucket_name="test",
                s3_verify=False,
                kafka_bootstrap_servers=kafka_bootstrap_servers,
                kafka_moderation_request_topic=kafka_moderation_request_topic,
                kafka_moderation_response_topic=kafka_moderation_response_topic,
                kafka_consumer_group_id=kafka_consumer_group_id,
            )
