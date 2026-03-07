"""Unit tests for Kafka producer."""

from unittest.mock import AsyncMock, patch

import pytest

from modservice.grpc.moderation_pb2 import ModerateObjectRequest, ObjectType
from modservice.kafka.producer import KafkaProducer


class TestKafkaProducer:
    """Test suite for KafkaProducer class."""

    @pytest.fixture
    def producer(self) -> KafkaProducer:
        """Create a KafkaProducer instance for testing."""
        return KafkaProducer(
            bootstrap_servers="localhost:9092",
            request_topic="moderation.requests",
        )

    @pytest.mark.asyncio
    async def test_start_initializes_producer(
        self, producer: KafkaProducer
    ) -> None:
        """Test that start() initializes the AIOKafkaProducer connection."""
        with patch(
            "modservice.kafka.producer.AIOKafkaProducer"
        ) as mock_producer_class:
            mock_producer_instance = AsyncMock()
            mock_producer_class.return_value = mock_producer_instance

            await producer.start()

            mock_producer_class.assert_called_once_with(
                bootstrap_servers="localhost:9092"
            )
            mock_producer_instance.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_closes_producer(self, producer: KafkaProducer) -> None:
        """Test that stop() closes the producer connection."""
        with patch(
            "modservice.kafka.producer.AIOKafkaProducer"
        ) as mock_producer_class:
            mock_producer_instance = AsyncMock()
            mock_producer_class.return_value = mock_producer_instance

            await producer.start()
            await producer.stop()

            mock_producer_instance.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_without_start_does_nothing(
        self, producer: KafkaProducer
    ) -> None:
        """Test that stop() does nothing if producer was never started."""
        # Should not raise an exception
        await producer.stop()

    @pytest.mark.asyncio
    async def test_send_moderation_request_serializes_and_sends(
        self, producer: KafkaProducer
    ) -> None:
        """Test that send_moderation_request serializes and sends the message."""
        with patch(
            "modservice.kafka.producer.AIOKafkaProducer"
        ) as mock_producer_class:
            mock_producer_instance = AsyncMock()
            mock_producer_class.return_value = mock_producer_instance

            await producer.start()

            # Send a moderation request
            await producer.send_moderation_request(
                object_id=123,
                object_type=ObjectType.OBJECT_TYPE_MOD_DESCRIPTION,
                text="Test mod title Test mod description",
            )

            # Verify send was called
            mock_producer_instance.send.assert_called_once()
            call_args = mock_producer_instance.send.call_args

            # Verify topic (first positional argument)
            assert call_args[0][0] == "moderation.requests"

            # Verify message can be deserialized (keyword argument 'value')
            message_bytes = call_args[1]["value"]
            request = ModerateObjectRequest()
            request.ParseFromString(message_bytes)

            assert request.id == 123
            assert request.type == ObjectType.OBJECT_TYPE_MOD_DESCRIPTION
            assert request.text == "Test mod title Test mod description"

            # Verify key is encoded correctly (keyword argument 'key')
            key_bytes = call_args[1]["key"]
            object_id = int.from_bytes(key_bytes, byteorder="big")
            assert object_id == 123

    @pytest.mark.asyncio
    async def test_send_moderation_request_without_start_raises_error(
        self, producer: KafkaProducer
    ) -> None:
        """Test that send_moderation_request raises error if producer not started."""
        with pytest.raises(RuntimeError, match="Producer not started"):
            await producer.send_moderation_request(
                object_id=123,
                object_type=ObjectType.OBJECT_TYPE_MOD_DESCRIPTION,
                text="Test text",
            )

    @pytest.mark.asyncio
    async def test_send_moderation_request_with_empty_text(
        self, producer: KafkaProducer
    ) -> None:
        """Test that send_moderation_request handles empty text."""
        with patch(
            "modservice.kafka.producer.AIOKafkaProducer"
        ) as mock_producer_class:
            mock_producer_instance = AsyncMock()
            mock_producer_class.return_value = mock_producer_instance

            await producer.start()

            # Send with empty text
            await producer.send_moderation_request(
                object_id=456,
                object_type=ObjectType.OBJECT_TYPE_MOD_DESCRIPTION,
                text="",
            )

            # Verify send was called
            mock_producer_instance.send.assert_called_once()
            call_args = mock_producer_instance.send.call_args

            # Verify message (keyword argument 'value')
            message_bytes = call_args[1]["value"]
            request = ModerateObjectRequest()
            request.ParseFromString(message_bytes)

            assert request.id == 456
            assert request.text == ""

    @pytest.mark.asyncio
    async def test_send_moderation_request_with_special_characters(
        self, producer: KafkaProducer
    ) -> None:
        """Test that send_moderation_request handles special characters in text."""
        with patch(
            "modservice.kafka.producer.AIOKafkaProducer"
        ) as mock_producer_class:
            mock_producer_instance = AsyncMock()
            mock_producer_class.return_value = mock_producer_instance

            await producer.start()

            special_text = "Test with émojis 🎮 and symbols !@#$%"
            await producer.send_moderation_request(
                object_id=789,
                object_type=ObjectType.OBJECT_TYPE_MOD_DESCRIPTION,
                text=special_text,
            )

            # Verify message
            call_args = mock_producer_instance.send.call_args
            message_bytes = call_args[1]["value"]
            request = ModerateObjectRequest()
            request.ParseFromString(message_bytes)

            assert request.id == 789
            assert request.text == special_text
