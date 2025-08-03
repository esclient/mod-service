import grpc

from modservice.grpc import mod_pb2


def TestMod(
    _: mod_pb2.TestModRequest, __: grpc.ServicerContext
) -> mod_pb2.TestModResponse:
    return mod_pb2.TestModResponse(success=True)
