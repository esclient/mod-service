import grpc

from modservice.constants import STATUS_BANNED, STATUS_HIDDEN, STATUS_UPLOADED
from modservice.grpc import mod_pb2
from modservice.service.service import ModService

_ENUM_TO_DB_STATUS_BY_VALUE: dict[int, str] = {
    mod_pb2.ModStatus.MOD_STATUS_UPLOADED: STATUS_UPLOADED,
    mod_pb2.ModStatus.MOD_STATUS_BANNED: STATUS_BANNED,
    mod_pb2.ModStatus.MOD_STATUS_HIDDEN: STATUS_HIDDEN,
}


def _convert_enum_to_status(status_value: int) -> str:
    if status_value == mod_pb2.ModStatus.MOD_STATUS_UNSPECIFIED:
        raise ValueError("Status must be specified")
    return _ENUM_TO_DB_STATUS_BY_VALUE[status_value]


async def SetStatus(
    service: ModService,
    request: mod_pb2.SetStatusRequest,
    context: grpc.ServicerContext,  # noqa: ARG001
) -> mod_pb2.SetStatusResponse:
    try:
        status_str = _convert_enum_to_status(request.status)
        success = await service.set_status(request.mod_id, status_str)
        return mod_pb2.SetStatusResponse(success=success)
    except ValueError as e:
        context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
        context.set_details(str(e))
        return mod_pb2.SetStatusResponse(success=False)
    except Exception as e:
        context.set_code(grpc.StatusCode.INTERNAL)
        context.set_details(f"Failed to set status: {e!s}")
        return mod_pb2.SetStatusResponse(success=False)
