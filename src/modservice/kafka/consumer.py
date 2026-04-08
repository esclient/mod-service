"""Kafka consumer for receiving moderation responses."""

import logging
import threading
from collections.abc import Callable

from confluent_kafka import Consumer, KafkaError, KafkaException, Message

from modservice.grpc import moderation_pb2

from .config import KafkaConfig

logger = logging.getLogger(__name__)


class KafkaConsumer:

    def __init__(
        self,
        config: KafkaConfig,
        callback: (
            Callable[[moderation_pb2.ModerateObjectResponse, int], None] | None
        ),
    ) -> None:

        self.config = config
        self.callback = callback
        self.consumer = Consumer(config.get_consumer_config())
        self.topic = config.result_topic
        self.running = False
        self.consumer_thread: threading.Thread | None = None

        self.consumer.subscribe([self.topic])
        logger.info(f"KafkaConsumer subscribed to topic: {self.topic}")

    def start(self) -> None:

        if self.running:
            logger.warning("Consumer already running")
            return

        self.running = True
        self.consumer_thread = threading.Thread(
            target=self._consume_loop, daemon=True
        )
        self.consumer_thread.start()
        logger.info("KafkaConsumer started")

    def stop(self) -> None:

        if not self.running:
            return

        self.running = False

        if self.consumer_thread and self.consumer_thread.is_alive():
            self.consumer_thread.join(timeout=5.0)

        self.consumer.close()
        logger.info("KafkaConsumer stopped")

    def _consume_loop(self) -> None:

        logger.info("Consumer loop started")

        while self.running:
            try:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue
                error = msg.error()
                if error is not None:
                    if error.code() == KafkaError._PARTITION_EOF:
                        logger.debug(
                            f"Reached end of partition for topic {msg.topic()}"
                        )
                    elif error.code() == KafkaError._TIMED_OUT:
                        logger.debug("Timeout")
                    else:
                        logger.error(f"Consumer error: {error}")
                    continue

                self._process_message(msg)

            except KafkaException as e:
                logger.error(f"Kafka exception in consume loop: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in consume loop: {e}")

        logger.info("Consumer loop ended")

    def _process_message(self, msg: Message) -> None:

        try:
            object_id = 0
            message_key = msg.key()
            if message_key is not None:
                try:
                    key_str = (
                        message_key.decode("utf-8")
                        if isinstance(message_key, bytes)
                        else message_key
                    )
                    object_id = int(key_str)
                except ValueError as e:
                    logger.error(
                        f"Failed to parse message key to request ID: {e}"
                    )
                    return

            message_value = msg.value()
            if message_value is None:
                logger.error("Received message without payload")
                return
            if not isinstance(message_value, bytes):
                logger.error("Received message payload with unexpected type")
                return

            response = moderation_pb2.ModerateObjectResponse()
            response.ParseFromString(message_value)

            logger.info(
                f"Received moderation response: object_id={object_id}, "
                f"success={response.success}"
            )

            if self.callback:
                try:
                    self.callback(response, object_id)
                except Exception as e:
                    logger.error(f"Error in callback: {e}")

        except Exception as e:
            logger.error(f"Failed to process message: {e}")

    def is_running(self) -> bool:
        return self.running
