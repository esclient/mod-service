"""Moderation service coordination layer."""

import asyncio
import logging
from concurrent.futures import Future

from modservice.grpc import moderation_pb2
from modservice.kafka.config import KafkaConfig
from modservice.kafka.consumer import KafkaConsumer
from modservice.kafka.producer import KafkaProducer
from modservice.repository.repository import ModRepository

logger = logging.getLogger(__name__)


class ModerationService:
    def __init__(
        self, repo: ModRepository, loop: asyncio.AbstractEventLoop
    ) -> None:
        self.config = KafkaConfig()
        self._repo = repo
        self._loop = loop

        self.producer = KafkaProducer(self.config)
        self.consumer = KafkaConsumer(
            self.config, callback=self._handle_moderation_response
        )

        self.consumer.start()

        logger.info("ModerationService initialized")

    def send_moderation_request(
        self, mod_id: int, title: str, description: str
    ) -> bool:
        try:
            request = moderation_pb2.ModerateObjectRequest()
            request.id = mod_id
            request.text = f"{title} {description}"
            request.type = moderation_pb2.OBJECT_TYPE_MOD_DESCRIPTION

            success = self.producer.send_moderation_request(request)

            if success:
                logger.info(f"Moderation request sent: mod_id={mod_id}")
            else:
                logger.error(
                    f"Failed to send moderation request: mod_id={mod_id}"
                )

            return success

        except Exception as e:
            logger.error(f"Error requesting moderation: {e}")
            return False

    def _handle_moderation_response(
        self, response: moderation_pb2.ModerateObjectResponse, object_id: int
    ) -> None:
        try:
            approved = response.success

            logger.info(
                f"Moderation result received: mod_id={object_id}, "
                f"approved={approved}"
            )

            self._update_mod_status(object_id, approved)

        except Exception as e:
            logger.error(f"Error handling moderation response: {e}")

    def _update_mod_status(self, mod_id: int, approved: bool) -> None:
        new_status = "UPLOADED" if approved else "HIDDEN"

        logger.info(
            f"Updating mod status: mod_id={mod_id}, approved={approved}, new_status={new_status}"
        )

        coroutine = self._repo.set_status(mod_id, new_status)

        future: Future[bool] = asyncio.run_coroutine_threadsafe(
            coroutine, self._loop
        )

        def _log_result(done_future: Future[bool]) -> None:
            try:
                success = done_future.result()
                if not success:
                    logger.error(
                        f"Failed to update mod status: mod_id={mod_id}"
                    )
                else:
                    logger.info(
                        f"Successfully updated mod status: mod_id={mod_id}, status={new_status}"
                    )
            except Exception as e:
                logger.error(f"Error updating mod status: {e}")

        future.add_done_callback(_log_result)

    def shutdown(self) -> None:
        self.consumer.stop()
        self.producer.flush()
        logger.info("ModerationService shutdown complete")
