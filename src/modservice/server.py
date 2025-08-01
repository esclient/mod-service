import grpc
from concurrent import futures
from grpc_reflection.v1alpha import reflection
from modservice.handler.handler import ModHandler
from modservice.grpc import mod_pb2_grpc
from modservice.grpc import mod_pb2
from modservice.settings import settings

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_worker=5))
    mod_pb2_grpc.add_ModServiceServicer_to_server(
        ModHandler(), server
    )

    SERVICE_NAMES = (
        mod_pb2.DESCRIPTOR.services_by_name["ModService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    server.add_insecure_port(f"{settings.host}:{settings.port}")
    server.start()
    print(f"gRPC server listening on {settings.host}:{settings.port}")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()