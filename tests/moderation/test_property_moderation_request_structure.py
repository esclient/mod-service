"""Property-based tests for moderation request message structure.

**Feature: mod-kafka-moderation**
"""

from unittest.mock import AsyncMock, Mock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from modservice.grpc.moderation_pb2 import ModerateObjectRequest, ObjectType
from modservice.moderation.moderation_service import ModerationService


class TestModerationRequestMessageStructureProperty:
    """Property-based tests for moderation request message structure.

    **Validates: Requirements 4.2, 4.3, 4.4, 4.5, 6.3, 9.1**
    """

    @given(
        mod_id=st.integers(min_value=1, max_value=1000000),
        title=st.text(min_size=1, max_size=255),
        description=st.text(min_size=1, max_size=1000),
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_property_3_moderation_request_message_structure(
        self,
        mod_id: int,
        title: str,
        description: str,
    ) -> None:
        """Property 3: Moderation request message structure.

        **Feature: mod-kafka-moderation, Property 3: For any mod with title
        and description, when a moderation request is sent, the resulting
        ModerateObjectRequest message should have correct id, type, and text
        fields**

        For any mod with title and description, when a moderation request is sent,
        the resulting ModerateObjectRequest message should have:
        - id field equal to the mod_id
        - type field equal to OBJECT_TYPE_MOD_DESCRIPTION
        - text field equal to "{title} {description}" (title and description separated by exactly one space)
        """
        # Track the message that was sent
        captured_message = None

        async def capture_send_moderation_request(  # noqa: RUF029
            object_id: int, object_type: ObjectType, text: str
        ) -> None:
            nonlocal captured_message
            # Create the actual protobuf message that would be sent
            captured_message = ModerateObjectRequest(
                id=object_id, type=object_type, text=text
            )

        # Mock producer that captures the message
        mock_producer = Mock()
        mock_producer.send_moderation_request = AsyncMock(
            side_effect=capture_send_moderation_request
        )

        # Mock repository (not used in this test)
        mock_repository = Mock()

        # Create moderation service
        moderation_service = ModerationService(mock_producer, mock_repository)

        # Send moderation request
        await moderation_service.send_moderation_request(
            mod_id, title, description
        )

        # Assert message was created
        assert (
            captured_message is not None
        ), "Moderation request message should be created"

        # Assert message.id == mod_id
        assert (
            captured_message.id == mod_id
        ), f"Message id should be {mod_id}, got {captured_message.id}"

        # Assert message.type == OBJECT_TYPE_MOD_DESCRIPTION
        assert (
            captured_message.type == ObjectType.OBJECT_TYPE_MOD_DESCRIPTION
        ), f"Message type should be OBJECT_TYPE_MOD_DESCRIPTION, got {captured_message.type}"

        # Assert message.text == f"{title} {description}"
        expected_text = f"{title} {description}"
        assert (
            captured_message.text == expected_text
        ), f"Message text should be '{expected_text}', got '{captured_message.text}'"
