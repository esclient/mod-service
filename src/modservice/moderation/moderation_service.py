"""Moderation service coordination layer."""

import logging

from modservice.grpc.moderation_pb2 import ObjectType
from modservice.kafka.producer import KafkaProducer
from modservice.repository.repository import ModRepository


class ModerationService:
    """Service layer that coordinates moderation requests and responses.

    This service bridges the Kafka producer/consumer with the repository,
    handling the sending of moderation requests and processing of responses.
    """

    def __init__(self, producer: KafkaProducer, repository: ModRepository):
        """Initialize the moderation service.

        Args:
            producer: Kafka producer for sending moderation requests
            repository: Repository for updating mod status
        """
        self._producer = producer
        self._repository = repository
        self._logger = logging.getLogger(__name__)

    async def send_moderation_request(
        self, mod_id: int, title: str, description: str
    ) -> None:
        """Send moderation request for a mod.

        Combines title and description with a single space separator and sends
        the request to the moderation service via Kafka. This is a fire-and-forget
        operation - failures are logged but do not raise exceptions.

        Args:
            mod_id: ID of the mod to moderate
            title: Mod title
            description: Mod description
        """
        text = f"{title} {description}"
        try:
            await self._producer.send_moderation_request(
                object_id=mod_id,
                object_type=ObjectType.OBJECT_TYPE_MOD_DESCRIPTION,
                text=text,
            )
            self._logger.info(f"Sent moderation request for mod {mod_id}")
        except Exception as e:
            self._logger.error(
                f"Failed to send moderation request for mod {mod_id}: {e}"
            )

    async def process_moderation_response(
        self, object_id: int, approved: bool
    ) -> None:
        """Process moderation response and update mod status.

        Maps the approved boolean to the appropriate mod status:
        - approved=True -> status="UPLOADED"
        - approved=False -> status="BANNED"

        Args:
            object_id: ID of the mod (from the moderation response)
            approved: Whether the content was approved by moderation
        """
        new_status = "UPLOADED" if approved else "BANNED"
        self._logger.info(
            f"Processing moderation response for mod {object_id}: "
            f"approved={approved}, new_status={new_status}"
        )
        try:
            success = await self._repository.set_status(object_id, new_status)
            if success:
                self._logger.info(
                    f"Updated mod {object_id} status to {new_status}"
                )
            else:
                self._logger.warning(
                    f"Mod {object_id} not found for status update"
                )
        except Exception as e:
            self._logger.error(f"Failed to update mod {object_id} status: {e}")
