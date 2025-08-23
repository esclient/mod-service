import grpc

from modservice.grpc import mod_pb2
from modservice.service.service import ModService

def CreateMod(
    service: ModService,
    request: mod_pb2.CreateModRequest,
    _: grpc.ServicerContext,
) -> mod_pb2.CreateModResponse:
    id = service.create_mod(
        request.mod_title, request.author_id, request.filename, request.description
    )
    return mod_pb2.CreateModResponse(
        mod_id=id, upload_url= , s3_key= 
    )
