import grpc

from modservice.grpc import mod_pb2


def TestMod(
    _: mod_pb2.CreateModRequest, __: grpc.ServicerContext
) -> mod_pb2.CreateModResponse:
    return mod_pb2.CreateModResponse(
        mod_id = 787465421214543,
        upload_url= "https//idontknowthelink.com",
        s3_key= "аф5ыа53аыфв4фы5в4ц86ав432афы35й"
    )
