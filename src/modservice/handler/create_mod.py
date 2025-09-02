import grpc

from modservice.grpc import mod_pb2
from modservice.service.service import ModService


def CreateMod(
    service: ModService,
    request: mod_pb2.CreateModRequest,
    context: grpc.ServicerContext,  # noqa: ARG001
) -> mod_pb2.CreateModResponse:
    # Создаем мод
    mod_id, s3_key, upload_url = service.create_mod(
        request.mod_title,
        request.author_id,
        request.description,
    )

    return mod_pb2.CreateModResponse(
        mod_id=mod_id, upload_url=upload_url, s3_key=s3_key
    )
