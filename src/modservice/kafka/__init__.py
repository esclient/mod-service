"""Kafka components for moderation integration."""

from modservice.kafka.consumer import KafkaConsumer
from modservice.kafka.producer import KafkaProducer

__all__ = ["KafkaConsumer", "KafkaProducer"]
