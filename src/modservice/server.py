import logging
from concurrent import futures

import grpc
from grpc_reflection.v1alpha import reflection

from modservice.grpc import mod_pb2, mod_pb2_grpc
from modservice.handler.handler import ModHandler
from modservice.settings import Settings


def serve() -> None:
    settings = Settings()
    settings.configure_logging()
    logger = logging.getLogger(__name__)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    mod_pb2_grpc.add_ModServiceServicer_to_server(
        ModHandler(), server
    )  # type: ignore[no-untyped-call]

    SERVICE_NAMES = (
        mod_pb2.DESCRIPTOR.services_by_name["ModService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    server.add_insecure_port(f"{settings.host}:{settings.port}")
    server.start()
    logger.info(f"gRPC server listening on {settings.host}:{settings.port}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
