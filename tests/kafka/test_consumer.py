"""Unit tests for Kafka consumer."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modservice.grpc.moderation_pb2 import ModerateObjectResponse
from modservice.kafka.consumer import KafkaConsumer


class TestKafkaConsumer:
    """Test suite for KafkaConsumer class."""

    @pytest.fixture
    def mock_moderation_service(self) -> AsyncMock:
        """Create a mock ModerationService for testing."""
        service = AsyncMock()
        service.process_moderation_response = AsyncMock()
        return service

    @pytest.fixture
    def consumer(self, mock_moderation_service: AsyncMock) -> KafkaConsumer:
        """Create a KafkaConsumer instance for testing."""
        return KafkaConsumer(
            bootstrap_servers="localhost:9092",
            response_topic="moderation.responses",
            group_id="test-group",
            moderation_service=mock_moderation_service,
        )

    @pytest.mark.asyncio
    async def test_start_initializes_consumer(
        self, consumer: KafkaConsumer
    ) -> None:
        """Test that start() initializes the AIOKafkaConsumer connection."""
        with patch(
            "modservice.kafka.consumer.AIOKafkaConsumer"
        ) as mock_consumer_class:
            mock_consumer_instance = AsyncMock()
            mock_consumer_class.return_value = mock_consumer_instance

            await consumer.start()

            mock_consumer_class.assert_called_once_with(
                "moderation.responses",
                bootstrap_servers="localhost:9092",
                group_id="test-group",
            )
            mock_consumer_instance.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_closes_consumer(self, consumer: KafkaConsumer) -> None:
        """Test that stop() closes the consumer connection."""
        with patch(
            "modservice.kafka.consumer.AIOKafkaConsumer"
        ) as mock_consumer_class:
            mock_consumer_instance = AsyncMock()
            mock_consumer_class.return_value = mock_consumer_instance

            await consumer.start()
            await consumer.stop()

            mock_consumer_instance.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_without_start_does_nothing(
        self, consumer: KafkaConsumer
    ) -> None:
        """Test that stop() does nothing if consumer was never started."""
        # Should not raise an exception
        await consumer.stop()

    @pytest.mark.asyncio
    async def test_consume_messages_processes_response(
        self, consumer: KafkaConsumer, mock_moderation_service: AsyncMock
    ) -> None:
        """Test that consume_messages processes a valid moderation response."""
        with patch(
            "modservice.kafka.consumer.AIOKafkaConsumer"
        ) as mock_consumer_class:
            # Create a valid moderation response
            response = ModerateObjectResponse(success=True)
            message_bytes = response.SerializeToString()

            # Create message key (object_id as big-endian bytes)
            object_id = 123
            object_id_bytes = object_id.to_bytes(8, byteorder="big")

            # Create mock message
            mock_message = MagicMock()
            mock_message.value = message_bytes
            mock_message.key = object_id_bytes

            # Mock the consumer to yield one message then stop
            async def mock_aiter(self):  # noqa: RUF029
                yield mock_message

            mock_consumer_instance = AsyncMock()
            mock_consumer_instance.__aiter__ = mock_aiter
            mock_consumer_class.return_value = mock_consumer_instance

            await consumer.start()

            # Consume one message
            task = consumer.consume_messages()
            try:
                await task
            except StopAsyncIteration:
                pass

            # Verify the moderation service was called with correct parameters
            mock_moderation_service.process_moderation_response.assert_called_once_with(
                object_id=123, approved=True
            )

    @pytest.mark.asyncio
    async def test_consume_messages_handles_deserialization_failure(
        self, consumer: KafkaConsumer, mock_moderation_service: AsyncMock
    ) -> None:
        """Test that consume_messages handles deserialization failures gracefully."""
        with patch(
            "modservice.kafka.consumer.AIOKafkaConsumer"
        ) as mock_consumer_class:
            # Create an invalid message
            mock_message = MagicMock()
            mock_message.value = b"invalid protobuf data"
            mock_message.key = b"\x00\x00\x00\x00\x00\x00\x00\x7b"

            # Mock the consumer to yield one message then stop
            async def mock_aiter(self):  # noqa: RUF029
                yield mock_message

            mock_consumer_instance = AsyncMock()
            mock_consumer_instance.__aiter__ = mock_aiter
            mock_consumer_class.return_value = mock_consumer_instance

            await consumer.start()

            # Consume one message - should not raise exception
            task = consumer.consume_messages()
            try:
                await task
            except StopAsyncIteration:
                pass

            # Verify the moderation service was NOT called
            mock_moderation_service.process_moderation_response.assert_not_called()

    @pytest.mark.asyncio
    async def test_consume_messages_extracts_object_id_from_key(
        self, consumer: KafkaConsumer, mock_moderation_service: AsyncMock
    ) -> None:
        """Test that consume_messages correctly extracts object_id from message key."""
        with patch(
            "modservice.kafka.consumer.AIOKafkaConsumer"
        ) as mock_consumer_class:
            # Create a valid moderation response
            response = ModerateObjectResponse(success=False)
            message_bytes = response.SerializeToString()

            # Create message key with specific object_id
            object_id = 456
            object_id_bytes = object_id.to_bytes(8, byteorder="big")

            mock_message = MagicMock()
            mock_message.value = message_bytes
            mock_message.key = object_id_bytes

            # Mock the consumer
            async def mock_aiter(self):  # noqa: RUF029
                yield mock_message

            mock_consumer_instance = AsyncMock()
            mock_consumer_instance.__aiter__ = mock_aiter
            mock_consumer_class.return_value = mock_consumer_instance

            await consumer.start()

            # Consume one message
            task = consumer.consume_messages()
            try:
                await task
            except StopAsyncIteration:
                pass

            # Verify the correct object_id was extracted
            mock_moderation_service.process_moderation_response.assert_called_once_with(
                object_id=456, approved=False
            )

    @pytest.mark.asyncio
    async def test_consume_messages_handles_processing_exception(
        self, consumer: KafkaConsumer, mock_moderation_service: AsyncMock
    ) -> None:
        """Test that consume_messages handles processing exceptions gracefully."""
        with patch(
            "modservice.kafka.consumer.AIOKafkaConsumer"
        ) as mock_consumer_class:
            # Create a valid moderation response
            response = ModerateObjectResponse(success=True)
            message_bytes = response.SerializeToString()
            object_id_bytes = (789).to_bytes(8, byteorder="big")

            mock_message = MagicMock()
            mock_message.value = message_bytes
            mock_message.key = object_id_bytes

            # Make the moderation service raise an exception
            mock_moderation_service.process_moderation_response.side_effect = (
                Exception("Processing error")
            )

            # Mock the consumer
            async def mock_aiter(self):  # noqa: RUF029
                yield mock_message

            mock_consumer_instance = AsyncMock()
            mock_consumer_instance.__aiter__ = mock_aiter
            mock_consumer_class.return_value = mock_consumer_instance

            await consumer.start()

            # Consume one message - should not raise exception
            task = consumer.consume_messages()
            try:
                await task
            except StopAsyncIteration:
                pass

            # Verify the moderation service was called
            mock_moderation_service.process_moderation_response.assert_called_once()
