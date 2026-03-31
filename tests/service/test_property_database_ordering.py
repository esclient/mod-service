"""Property-based tests for database operation ordering.

**Feature: mod-kafka-moderation**
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from modservice.moderation.moderation_service import ModerationService
from modservice.repository.repository import ModRepository
from modservice.service.s3_service import S3Service
from modservice.service.service import ModService


class TestDatabaseOperationOrdering:
    """Property-based tests for database operation ordering.

    **Validates: Requirements 9.2**
    """

    @given(
        title=st.text(min_size=1, max_size=255),
        author_id=st.integers(min_value=1, max_value=1000000),
        description=st.text(min_size=0, max_size=1000),
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_property_8_database_operation_ordering(
        self,
        title: str,
        author_id: int,
        description: str,
    ) -> None:
        """Property 8: Database operation ordering.

        **Feature: mod-kafka-moderation, Property 8: For any mod creation, the
        mod record should exist in the database before the moderation request
        is sent**

        For any mod creation, the mod record should exist in the database with
        status UPLOADING before the moderation request is sent to Kafka.
        """
        # Track the order of operations
        operation_order: list[str] = []

        # Mock database pool and connection
        mod_id = 789
        s3_key = f"mods/{author_id}/test-key"
        upload_url = "https://s3.example.com/upload"

        # Mock the repository's create_mod to track database insert timing
        async def mock_create_mod(  # noqa: RUF029
            *args: object, **kwargs: object
        ) -> int:
            operation_order.append("database_insert")
            return mod_id

        conn = Mock()
        conn.fetchval = AsyncMock(side_effect=mock_create_mod)
        acquire_cm = AsyncMock()
        acquire_cm.__aenter__.return_value = conn
        acquire_cm.__aexit__.return_value = None
        pool = Mock()
        pool.acquire.return_value = acquire_cm

        repo = ModRepository(pool)

        # Mock S3 service
        s3_service = Mock(spec=S3Service)
        s3_service.generate_mod_upload_url = AsyncMock(return_value=upload_url)

        # Mock repository's insert_s3_key using patch
        with patch.object(
            repo, "insert_s3_key", new=AsyncMock(return_value=s3_key)
        ):
            # Mock Kafka producer to track send timing
            def mock_send_moderation_request(  # noqa: RUF029
                *args: object, **kwargs: object
            ) -> bool:
                operation_order.append("kafka_send")
                return True

            kafka_producer = Mock()
            kafka_producer.send_moderation_request = Mock(
                side_effect=mock_send_moderation_request
            )

            # Create real moderation service with mocked producer
            moderation_service = ModerationService(kafka_producer, repo)

            # Create service and call create_mod
            service = ModService(repo, s3_service, moderation_service)
            result_mod_id, result_s3_key, result_upload_url = (
                await service.create_mod(title, author_id, description)
            )

            # Assert the mod was created successfully
            assert (
                result_mod_id == mod_id
            ), "create_mod should return the mod_id"
            assert (
                result_s3_key == s3_key
            ), "create_mod should return the s3_key"
            assert (
                result_upload_url == upload_url
            ), "create_mod should return the upload_url"

            # Assert both operations were called
            assert (
                len(operation_order) == 2
            ), "Both database insert and Kafka send should be called"

        # Assert database insert happened before Kafka send
        assert (
            operation_order[0] == "database_insert"
        ), "Database insert should happen first"
        assert (
            operation_order[1] == "kafka_send"
        ), "Kafka send should happen after database insert"

        # Verify the database insert was called
        assert (
            conn.fetchval.await_count == 1
        ), "Database insert should be called exactly once"

        # Verify the Kafka producer was called
        assert (
            kafka_producer.send_moderation_request.await_count == 1
        ), "Kafka send should be called exactly once"

        # Verify the Kafka producer was called with correct parameters
        kafka_call_args = kafka_producer.send_moderation_request.await_args
        assert (
            kafka_call_args.kwargs["object_id"] == mod_id
        ), f"Kafka send should use mod_id {mod_id}"
        assert (
            kafka_call_args.kwargs["text"] == f"{title} {description}"
        ), f"Kafka send should use combined text '{title} {description}'"
