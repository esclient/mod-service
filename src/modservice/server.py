import asyncio
import logging
from concurrent import futures

import asyncpg
import grpc
from grpc_reflection.v1alpha import reflection

from modservice.grpc import mod_pb2, mod_pb2_grpc
from modservice.handler.handler import ModHandler
from modservice.kafka.consumer import KafkaConsumer
from modservice.kafka.producer import KafkaProducer
from modservice.moderation.moderation_service import ModerationService
from modservice.repository.repository import ModRepository
from modservice.s3_client import S3Client
from modservice.service.s3_service import S3Service
from modservice.service.service import ModService
from modservice.settings import Settings


async def serve() -> None:
    settings = Settings()
    settings.configure_logging()
    logger = logging.getLogger(__name__)

    db_pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=1,
        max_size=10,
    )

    s3_client = S3Client(
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        endpoint_url=settings.s3_api_endpoint,
        bucket_name=settings.s3_bucket_name,
        verify=settings.s3_verify,
    )

    s3_service = S3Service(s3_client)

    repo = ModRepository(db_pool)

    # Initialize Kafka producer
    producer = KafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        request_topic=settings.kafka_moderation_request_topic,
    )
    await producer.start()

    # Create moderation service
    moderation_service = ModerationService(producer, repo)

    # Initialize Kafka consumer
    consumer = KafkaConsumer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        response_topic=settings.kafka_moderation_response_topic,
        group_id=settings.kafka_consumer_group_id,
        moderation_service=moderation_service,
    )
    await consumer.start()

    # Start consumer in background task
    consumer_task = asyncio.create_task(consumer.consume_messages())

    # Create service with moderation service
    service = ModService(repo, s3_service, moderation_service)
    handler = ModHandler(service)

    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=5))
    mod_pb2_grpc.add_ModServiceServicer_to_server(
        handler, server
    )  # type: ignore[no-untyped-call]

    SERVICE_NAMES = (
        mod_pb2.DESCRIPTOR.services_by_name["ModService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    server.add_insecure_port(f"{settings.host}:{settings.port}")
    await server.start()
    logger.info(f"gRPC server listening on {settings.host}:{settings.port}")

    try:
        await server.wait_for_termination()
    finally:
        # Gracefully shutdown Kafka components
        consumer_task.cancel()
        await producer.stop()
        await consumer.stop()


def main() -> None:
    asyncio.run(serve())


if __name__ == "__main__":
    main()
