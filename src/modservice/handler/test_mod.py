import grpc

from modservice.grpc import mod_pb2


def TestMod(
    _: mod_pb2.CreateModRequest, __: grpc.ServicerContext
) -> mod_pb2.CreateModResponse:
    return mod_pb2.CreateModResponse(success=True)
