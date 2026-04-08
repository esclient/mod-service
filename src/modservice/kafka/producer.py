"""Kafka producer for sending moderation requests."""

import logging

from confluent_kafka import KafkaError, KafkaException, Message, Producer

from modservice.grpc import moderation_pb2

from .config import KafkaConfig

logger = logging.getLogger(__name__)


class KafkaProducer:

    def __init__(self, config: KafkaConfig) -> None:
        self.config = config
        self.producer = Producer(config.get_producer_config())
        self.topic = config.request_topic

        logger.info(f"KafkaProducer initialized for topic: {self.topic}")

    def send_moderation_request(
        self, request: moderation_pb2.ModerateObjectRequest, retries: int = 3
    ) -> bool:
        for _ in range(retries):
            try:
                serialized_request = request.SerializeToString()

                key = str(request.id).encode("utf-8")

                self.producer.produce(
                    topic=self.topic,
                    value=serialized_request,
                    key=key,
                    partition=-1,
                    on_delivery=self._delivery_callback,
                )

                self.producer.poll(0)

                logger.debug(
                    f"Moderation request queued: ID={request.id}, text_length={len(request.text)}"
                )
                return True

            except BufferError as e:
                logger.error(f"Producer buffer full, message not queued: {e}")
                return False
            except KafkaException as e:
                logger.error(f"Failed to produce message: {e}")
                return False
            except Exception as e:
                logger.error(f"Unexpected error producing message: {e}")
                return False
        return False

    def _delivery_callback(self, err: KafkaError | None, msg: Message) -> None:

        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(
                f"Message delivered: topic={msg.topic()}, "
                f"partition={msg.partition()}, offset={msg.offset()}"
            )

    def flush(self, timeout: float = 10.0) -> None:

        remaining = self.producer.flush(timeout)

        if remaining > 0:
            logger.warning(
                f"Flush incomplete: {remaining} messages still pending"
            )
        else:
            logger.debug("All messages flushed successfully")

    def __del__(self) -> None:
        if hasattr(self, "producer"):
            self.flush()
