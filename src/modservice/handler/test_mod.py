from modservice.grpc import mod_pb2
import grpc
from modservice.service.test_mod import test_mod as service_test_mod

def TestMod(request: mod_pb2.TestModRequest, contest: grpc.ServicerContext)
    success = service_test_mod(request.mod_id)
    return mod_pb2.TestModResponse(
        success = success
    )