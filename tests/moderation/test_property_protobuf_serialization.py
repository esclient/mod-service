"""Property-based tests for protobuf serialization round-trip.

**Feature: mod-kafka-moderation**
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from modservice.grpc.moderation_pb2 import ModerateObjectRequest, ObjectType


class TestProtobufSerializationProperty:
    """Property-based tests for protobuf serialization round-trip.

    **Validates: Requirements 4.6, 5.4**
    """

    @given(
        object_id=st.integers(min_value=1, max_value=1000000),
        object_type=st.sampled_from(
            [
                ObjectType.OBJECT_TYPE_UNSPECIFIED,
                ObjectType.OBJECT_TYPE_MOD_DESCRIPTION,
                ObjectType.OBJECT_TYPE_COMMENT_TEXT,
                ObjectType.OBJECT_TYPE_USER_NAME,
            ]
        ),
        text=st.text(min_size=0, max_size=10000),
    )
    @settings(max_examples=100)
    def test_property_4_protobuf_serialization_round_trip(
        self,
        object_id: int,
        object_type: ObjectType,
        text: str,
    ) -> None:
        """Property 4: Protobuf serialization round-trip.

        **Feature: mod-kafka-moderation, Property 4: For any valid
        ModerateObjectRequest message, serializing to bytes then deserializing
        should produce an equivalent message**

        For any valid ModerateObjectRequest message, serializing to bytes then
        deserializing should produce an equivalent message with all fields preserved.
        """
        # Create original message
        original_message = ModerateObjectRequest(
            id=object_id, type=object_type, text=text
        )

        # Serialize to bytes
        message_bytes = original_message.SerializeToString()

        # Deserialize from bytes
        deserialized_message = ModerateObjectRequest()
        deserialized_message.ParseFromString(message_bytes)

        # Assert all fields are preserved
        assert (
            deserialized_message.id == original_message.id
        ), f"Deserialized id should be {original_message.id}, got {deserialized_message.id}"

        assert (
            deserialized_message.type == original_message.type
        ), f"Deserialized type should be {original_message.type}, got {deserialized_message.type}"

        assert (
            deserialized_message.text == original_message.text
        ), f"Deserialized text should be '{original_message.text}', got '{deserialized_message.text}'"
