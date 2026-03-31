"""Property-based tests for initial mod status.

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


class TestInitialModStatusProperty:
    """Property-based tests for initial mod status.

    **Validates: Requirements 3.3**
    """

    @given(
        title=st.text(min_size=1, max_size=255),
        author_id=st.integers(min_value=1, max_value=1000000),
        description=st.text(min_size=0, max_size=1000),
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_property_1_initial_mod_status_is_uploading(
        self,
        title: str,
        author_id: int,
        description: str,
    ) -> None:
        """Property 1: Initial mod status is ON_MODERATION.

        **Feature: mod-kafka-moderation, Property 1: For any mod creation with
        valid title, author_id, and description, the mod's initial status in
        the database should be ON_MODERATION**

        For any mod creation with valid title, author_id, and description,
        the mod's initial status in the database should be ON_MODERATION.
        """
        # Mock database pool and connection
        mod_id = 123
        s3_key = f"mods/{author_id}/test-key"
        upload_url = "https://s3.example.com/upload"

        # Mock the repository's create_mod to capture the SQL call
        conn = Mock()
        conn.fetchval = AsyncMock(return_value=mod_id)
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
            # Mock moderation service
            moderation_service = Mock(spec=ModerationService)
            moderation_service.send_moderation_request = Mock(return_value=True)

            # Create service and call create_mod
            service = ModService(repo, s3_service, moderation_service)
            result_mod_id, result_s3_key, result_upload_url = (
                await service.create_mod(title, author_id, description)
            )

            # Assert the mod was created successfully
            assert result_mod_id == mod_id
            assert result_s3_key == s3_key
            assert result_upload_url == upload_url

            # Assert the SQL INSERT was called with status='ON_MODERATION'
            assert (
                conn.fetchval.await_count == 1
            ), "fetchval should be called exactly once"

            # Verify the SQL contains 'ON_MODERATION' as the status
            call_args = conn.fetchval.await_args.args
            sql = call_args[0]
            assert "'ON_MODERATION'" in sql, "SQL should set status to 'ON_MODERATION'"

            # Verify the parameters match
            assert (
                call_args[1] == author_id
            ), f"Author ID parameter should be {author_id}"
        assert call_args[2] == title, f"Title parameter should be {title}"
        assert (
            call_args[3] == description
        ), f"Description parameter should be {description}"
        assert call_args[4] == 1, "Version parameter should be 1"
