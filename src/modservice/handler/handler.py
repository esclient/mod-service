from modservice.grpc import mod_pb2_grpc
from modservice.handler.test_mod import TestMod


class ModHandler(mod_pb2_grpc.ModServiceServicer):
    TestMod = staticmethod(TestMod)
