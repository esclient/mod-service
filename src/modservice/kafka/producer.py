"""Kafka producer for sending moderation requests."""

import logging

from aiokafka import AIOKafkaProducer  # type: ignore[import-untyped]

from modservice.grpc.moderation_pb2 import ModerateObjectRequest, ObjectType


class KafkaProducer:
    """Kafka producer for sending moderation requests to the moderation service."""

    def __init__(self, bootstrap_servers: str, request_topic: str):
        """Initialize Kafka producer with connection settings.

        Args:
            bootstrap_servers: Kafka broker addresses (e.g., "localhost:9092")
            request_topic: Topic name for moderation requests
        """
        self._bootstrap_servers = bootstrap_servers
        self._request_topic = request_topic
        self._producer: AIOKafkaProducer | None = None
        self._logger = logging.getLogger(__name__)

    async def start(self) -> None:
        """Initialize Kafka producer connection.

        Establishes connection to the Kafka broker and prepares the producer
        for sending messages.
        """
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap_servers
        )
        await self._producer.start()
        self._logger.info(
            f"Kafka producer connected to {self._bootstrap_servers}"
        )

    async def stop(self) -> None:
        """Close Kafka producer connection.

        Gracefully shuts down the producer and closes the connection to the
        Kafka broker.
        """
        if self._producer:
            await self._producer.stop()

    async def send_moderation_request(
        self, object_id: int, object_type: ObjectType, text: str
    ) -> None:
        """Send moderation request message to Kafka.

        Args:
            object_id: ID of the object to moderate (e.g., mod_id)
            object_type: Type of object (e.g., OBJECT_TYPE_MOD_DESCRIPTION)
            text: Text content to moderate

        Raises:
            RuntimeError: If producer is not started
        """
        if not self._producer:
            raise RuntimeError("Producer not started. Call start() first.")

        request = ModerateObjectRequest(
            id=object_id, type=object_type, text=text
        )
        message_bytes = request.SerializeToString()
        # Encode object_id as message key (big-endian, 8 bytes)
        key_bytes = object_id.to_bytes(8, byteorder="big")
        await self._producer.send(
            self._request_topic, value=message_bytes, key=key_bytes
        )
        self._logger.info(f"Sent moderation request for object {object_id}")
