"""Kafka consumer for receiving moderation responses."""

import logging
from typing import TYPE_CHECKING

from aiokafka import AIOKafkaConsumer  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from modservice.moderation.moderation_service import ModerationService


class KafkaConsumer:
    """Kafka consumer for receiving moderation responses from the moderation service."""

    def __init__(
        self,
        bootstrap_servers: str,
        response_topic: str,
        group_id: str,
        moderation_service: "ModerationService",
    ):
        """Initialize Kafka consumer with connection settings.

        Args:
            bootstrap_servers: Kafka broker addresses (e.g., "localhost:9092")
            response_topic: Topic name for moderation responses
            group_id: Consumer group ID for coordinating multiple consumers
            moderation_service: ModerationService instance for processing responses
        """
        self._bootstrap_servers = bootstrap_servers
        self._response_topic = response_topic
        self._group_id = group_id
        self._moderation_service = moderation_service
        self._consumer: AIOKafkaConsumer | None = None
        self._logger = logging.getLogger(__name__)

    async def start(self) -> None:
        """Initialize Kafka consumer connection.

        Establishes connection to the Kafka broker and subscribes to the
        response topic.
        """
        self._consumer = AIOKafkaConsumer(
            self._response_topic,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
        )
        await self._consumer.start()
        self._logger.info(
            f"Kafka consumer subscribed to {self._response_topic} "
            f"with group {self._group_id}"
        )

    async def stop(self) -> None:
        """Close Kafka consumer connection.

        Gracefully shuts down the consumer and closes the connection to the
        Kafka broker.
        """
        if self._consumer:
            await self._consumer.stop()

    async def consume_messages(self) -> None:
        """Continuously consume and process moderation responses.

        This method runs in an infinite loop, processing messages as they arrive.
        Deserialization failures are logged and processing continues with the
        next message.
        """
        from modservice.grpc.moderation_pb2 import ModerateObjectResponse

        if not self._consumer:
            raise RuntimeError("Consumer not started. Call start() first.")

        async for message in self._consumer:
            try:
                # Deserialize the protobuf message
                response = ModerateObjectResponse()
                response.ParseFromString(message.value)

                # Extract object_id from message key (big endian encoding)
                object_id = int.from_bytes(message.key, byteorder="big")

                # Process the moderation response
                await self._moderation_service.process_moderation_response(
                    object_id=object_id, approved=response.success
                )
            except Exception as e:
                self._logger.error(
                    f"Failed to process moderation response: {e}",
                    exc_info=True,
                )
