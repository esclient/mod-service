"""Kafka producer for sending moderation requests."""

import logging

from aiokafka import AIOKafkaProducer  # type: ignore[import-untyped]

from modservice.grpc.moderation_pb2 import ModerateObjectRequest, ObjectType


class KafkaProducer:
    """Sends moderation requests to Kafka."""

    def __init__(self, bootstrap_servers: str, request_topic: str):
        """Set up Kafka producer.

        Args:
            bootstrap_servers: Kafka broker addresses like "localhost:9092"
            request_topic: Topic name for moderation requests
        """
        self._bootstrap_servers = bootstrap_servers
        self._request_topic = request_topic
        self._producer: AIOKafkaProducer | None = None
        self._logger = logging.getLogger(__name__)

    async def start(self) -> None:
        """Connect to Kafka broker and get ready to send messages."""
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap_servers
        )
        await self._producer.start()
        self._logger.info(
            f"Kafka producer connected to {self._bootstrap_servers}"
        )

    async def stop(self) -> None:
        """Shut down producer and close Kafka connection."""
        if self._producer:
            await self._producer.stop()

    async def send_moderation_request(
        self, object_id: int, object_type: ObjectType, text: str
    ) -> None:
        """Send moderation request to Kafka.

        Args:
            object_id: ID of the thing to moderate (mod_id, etc.)
            object_type: What kind of object (OBJECT_TYPE_MOD_DESCRIPTION, etc.)
            text: Text to check

        Raises:
            RuntimeError: If you forgot to call start() first
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
