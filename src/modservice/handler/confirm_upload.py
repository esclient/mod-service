import grpc

from modservice.grpc import mod_pb2
from modservice.service.service import ModService


def ConfirmUpload(
    service: ModService,
    request: mod_pb2.ConfirmUploadRequest,
    context: grpc.ServicerContext,  # noqa: ARG001
) -> mod_pb2.ConfirmUploadResponse:
    try:
        success = service.confirm_upload(request.mod_id)

        return mod_pb2.ConfirmUploadResponse(success=success)
    except Exception as e:
        context.set_code(grpc.StatusCode.INTERNAL)
        context.set_details(f"Failed to confirm upload: {e!s}")
        return mod_pb2.ConfirmUploadResponse(success=False)
