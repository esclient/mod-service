"""Property-based tests for status transition based on moderation result.

**Feature: mod-kafka-moderation**
"""

from unittest.mock import AsyncMock, Mock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from modservice.moderation.moderation_service import ModerationService


class TestStatusTransitionProperty:
    """Property-based tests for status transition based on moderation result.

    **Validates: Requirements 10.1, 10.2, 6.4**
    """

    @given(
        mod_id=st.integers(min_value=1, max_value=1000000),
        approved=st.booleans(),
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_property_6_status_transition_based_on_moderation_result(
        self,
        mod_id: int,
        approved: bool,
    ) -> None:
        """Property 6: Status transition based on moderation result.

        **Feature: mod-kafka-moderation, Property 6: For any moderation
        response, the resulting mod status should be UPLOADED if approved,
        BANNED if rejected**

        For any moderation response, the resulting mod status should be UPLOADED
        if the response indicates approval (approved=true), and BANNED if the
        response indicates rejection (approved=false).
        """
        # Track the status that was set
        captured_status = None
        captured_mod_id = None

        async def capture_set_status(  # noqa: RUF029
            object_id: int, status: str
        ) -> bool:
            nonlocal captured_status, captured_mod_id
            captured_mod_id = object_id
            captured_status = status
            return True  # Simulate successful update

        # Mock repository that captures the status update
        mock_repository = Mock()
        mock_repository.set_status = AsyncMock(side_effect=capture_set_status)

        # Mock producer (not used in this test)
        mock_producer = Mock()

        # Create moderation service
        moderation_service = ModerationService(mock_producer, mock_repository)

        # Process moderation response
        await moderation_service.process_moderation_response(mod_id, approved)

        # Assert set_status was called
        assert captured_status is not None, "set_status should be called"
        assert (
            captured_mod_id == mod_id
        ), f"set_status should be called with mod_id {mod_id}"

        # Assert correct status mapping
        expected_status = "UPLOADED" if approved else "BANNED"
        assert (
            captured_status == expected_status
        ), f"Status should be '{expected_status}' when approved={approved}, got '{captured_status}'"
