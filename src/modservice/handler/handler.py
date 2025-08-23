import grpc
from modservice.grpc import mod_pb2_grpc, mod_pb2
from modservice.service.service import ModService
from modservice.handler.create_mod import CreateMod as _create_mod

class ModHandler(mod_pb2_grpc.ModServiceServicer):
    def __init__(self, service: ModService):
        self._service = service

    def CreateComment(
        self,
        request: mod_pb2.CreateModRequest,
        context: grpc.ServicerContext,
    ) -> mod_pb2.CreateModResponse:
        return _create_mod(self._service, request, context)