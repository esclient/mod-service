import grpc

from modservice.grpc import mod_pb2
from modservice.service.service import ModService


async def GetDownloadLink(
    service: ModService,
    request: mod_pb2.GetModDownloadLinkRequest,
    context: grpc.ServicerContext,  # noqa: ARG001
) -> mod_pb2.GetModDownloadLinkResponse:
    link_url = await service.get_mod_download_link(request.mod_id)

    return mod_pb2.GetModDownloadLinkResponse(link_url=link_url)
