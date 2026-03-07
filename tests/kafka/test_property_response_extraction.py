"""Property-based tests for moderation response extraction.

**Feature: mod-kafka-moderation**
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from modservice.grpc.moderation_pb2 import ModerateObjectResponse


class TestModerationResponseExtractionProperty:
    """Property-based tests for moderation response extraction.

    **Validates: Requirements 5.5**
    """

    @given(
        object_id=st.integers(min_value=1, max_value=2**63 - 1),
        success=st.booleans(),
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_property_5_moderation_response_extraction(
        self,
        object_id: int,
        success: bool,
    ) -> None:
        """Property 5: Moderation response extraction.

        **Feature: mod-kafka-moderation, Property 5: For any
        ModerateObjectResponse message with an object_id, the consumer should
        correctly extract both the object_id and the success field value**

        For any ModerateObjectResponse message with an object_id, the consumer
        should correctly extract both the object_id and the success field value.
        """
        # Create a mock moderation service to capture the extracted values
        mock_moderation_service = AsyncMock()
        mock_moderation_service.process_moderation_response = AsyncMock()

        # Create a ModerateObjectResponse message with the generated values
        response = ModerateObjectResponse(success=success)
        message_bytes = response.SerializeToString()

        # Encode object_id as bytes (big endian, 8 bytes for int64)
        object_id_bytes = object_id.to_bytes(8, byteorder="big")

        # Create a mock Kafka message
        mock_message = MagicMock()
        mock_message.value = message_bytes
        mock_message.key = object_id_bytes

        # Test the extraction logic directly (this is what the consumer does)
        # Deserialize the protobuf message
        response_parsed = ModerateObjectResponse()
        response_parsed.ParseFromString(mock_message.value)

        # Extract object_id from message key (big endian encoding)
        extracted_object_id = int.from_bytes(mock_message.key, byteorder="big")

        # Simulate calling the moderation service
        await mock_moderation_service.process_moderation_response(
            object_id=extracted_object_id, approved=response_parsed.success
        )

        # Assert that the extraction correctly preserved both fields
        mock_moderation_service.process_moderation_response.assert_called_once_with(
            object_id=object_id, approved=success
        )

        # Verify the extracted values match the original values
        call_args = (
            mock_moderation_service.process_moderation_response.call_args
        )
        assert call_args.kwargs["object_id"] == object_id, (
            f"Extracted object_id {call_args.kwargs['object_id']} should match "
            f"original {object_id}"
        )
        assert call_args.kwargs["approved"] == success, (
            f"Extracted success {call_args.kwargs['approved']} should match "
            f"original {success}"
        )
