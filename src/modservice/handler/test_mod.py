from modservice.grpc import mod_pb2
import grpc

def TestMod(request: mod_pb2.TestModRequest, context: grpc.ServicerContext):
    return mod_pb2.TestModResponse(
        success = True
    )