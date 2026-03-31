"""Kafka consumer for receiving moderation responses."""

from confluent_kafka import Consumer, KafkaException, KafkaError
import logging
import threading
from .config import KafkaConfig
from modservice.grpc import moderation_pb2

logger = logging.getLogger(__name__)


class KafkaConsumer:

    def __init__(self, config: KafkaConfig, callback):

        self.config = config
        self.callback = callback
        self.consumer = Consumer(config.get_consumer_config())
        self.topic = config.result_topic
        self.running = False
        self.consumer_thread = None

        self.consumer.subscribe([self.topic])
        logger.info(f"KafkaConsumer subscribed to topic: {self.topic}")

    def start(self):

        if self.running:
            logger.warning("Consumer already running")
            return

        self.running = True
        self.consumer_thread = threading.Thread(target=self._consume_loop, daemon=True)
        self.consumer_thread.start()
        logger.info("KafkaConsumer started")

    def stop(self):

        if not self.running:
            return

        self.running = False

        if self.consumer_thread and self.consumer_thread.is_alive():
            self.consumer_thread.join(timeout=5.0)

        self.consumer.close()
        logger.info("KafkaConsumer stopped")

    def _consume_loop(self):

        logger.info("Consumer loop started")

        while self.running:
            try:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(f"Reached end of partition for topic {msg.topic()}")
                    elif msg.error().code() == KafkaError._TIMED_OUT:
                        logger.debug("Timeout")
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                    continue

                self._process_message(msg)

            except KafkaException as e:
                logger.error(f"Kafka exception in consume loop: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in consume loop: {e}")

        logger.info("Consumer loop ended")

    def _process_message(self, msg):

        try:
            object_id = 0
            if msg.key() is not None:
                try:
                    key_str = msg.key().decode('utf-8')
                    object_id = int(key_str)
                except ValueError as e:
                    logger.error(f"Failed to parse message key to request ID: {e}")
                    return

            response = moderation_pb2.ModerateObjectResponse()
            response.ParseFromString(msg.value())

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
