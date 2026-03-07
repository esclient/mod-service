import os


class KafkaConfig:

    def __init__(self):
        self.brokers = os.getenv('KAFKA_BROKERS', 'localhost:9092')
        self.request_topic = os.getenv('KAFKA_REQUEST_TOPIC', 'moderation-request')
        self.result_topic = os.getenv('KAFKA_RESULT', 'moderation-result')
        self.consumer_group_id = os.getenv('KAFKA_CONSUMER_GROUP_ID', 'mod-service-group')
        self.max_retries = int(os.getenv('KAFKA_MAX_RETRIES', '3'))
        self.retry_backoff_ms = int(os.getenv('KAFKA_RETRY_BACKOFF_MS', '1000'))
        self.enable_ssl = os.getenv('KAFKA_ENABLE_SSL', 'false').lower() == 'true'

    def get_producer_config(self):
        config = {
            'bootstrap.servers': self.brokers,
            'client.id': 'mod_service_producer',
            'acks': 'all',
            'retries': self.max_retries,
            'retry.backoff.ms': self.retry_backoff_ms,
            'enable.idempotence': True,
            'compression.type': 'none'
        }
        return config

    def get_consumer_config(self):
        config = {
            'bootstrap.servers': self.brokers,
            'group.id': self.consumer_group_id,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True,
            'auto.commit.interval.ms': 1000,
            'session.timeout.ms': 30000,
            'heartbeat.interval.ms': 10000
        }
        return config
