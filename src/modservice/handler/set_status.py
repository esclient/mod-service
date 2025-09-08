import grpc

from modservice.grpc import mod_pb2
from modservice.service.service import ModService


_ENUM_TO_DB_STATUS = {
    # Supported statuses
    "UPLOADING": "UPLOADING",
    "UPLOADED": "UPLOADED",
    "BANNED": "BANNED",
    "HIDDEN": "HIDDEN",
}


def _extract_status_string(request: object) -> str:
    # Backward compatible: current proto lacks status field
    if hasattr(request, "status"):
        status_value = getattr(request, "status")
        # If an enum exists in mod_pb2, prefer its Name() resolution
        enum_cls = getattr(mod_pb2, "ModStatus", None)
        if enum_cls is not None and isinstance(status_value, int):
            try:
                enum_name = enum_cls.Name(status_value)
                if enum_name in _ENUM_TO_DB_STATUS:
                    return _ENUM_TO_DB_STATUS[enum_name]
                raise ValueError(f"Unsupported status: {enum_name}")
            except Exception:
                pass

        # If it is already a string (some clients may pass stringly-typed), normalize
        if isinstance(status_value, str):
            enum_name = status_value.upper()
            if enum_name in _ENUM_TO_DB_STATUS:
                return _ENUM_TO_DB_STATUS[enum_name]
            raise ValueError(f"Unsupported status: {enum_name}")

    # Fallback to previous behavior
    return "UPLOADED"


def SetStatus(
    service: ModService,
    request: mod_pb2.ConfirmUploadRequest,
    context: grpc.ServicerContext,  # noqa: ARG001
) -> mod_pb2.ConfirmUploadResponse:
    try:
        status_str = _extract_status_string(request)
        success = service.set_status(request.mod_id, status_str)

        return mod_pb2.ConfirmUploadResponse(success=success)

    except ValueError as e:
        context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
        context.set_details(str(e))
        return mod_pb2.ConfirmUploadResponse(success=False)
    except Exception as e:
        context.set_code(grpc.StatusCode.INTERNAL)
        context.set_details(f"Failed to set status: {e!s}")

        return mod_pb2.ConfirmUploadResponse(success=False)


