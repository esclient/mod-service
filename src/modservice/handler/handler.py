import grpc

from modservice.grpc import mod_pb2, mod_pb2_grpc
from modservice.handler.create_mod import CreateMod as _create_mod
from modservice.handler.get_mod_download_link import (
    GetDownloadLink as _get_mod_download_link,
)
from modservice.handler.confirm_upload import (
    ConfirmUpload as _confirm_upload,
)
from modservice.service.service import ModService


class ModHandler(mod_pb2_grpc.ModServiceServicer):
    def __init__(self, service: ModService):
        self._service = service

    def CreateMod(
        self,
        request: mod_pb2.CreateModRequest,
        context: grpc.ServicerContext,
    ) -> mod_pb2.CreateModResponse:
        return _create_mod(self._service, request, context)

    def GetModDownloadLink(
        self,
        request: mod_pb2.GetModDownloadLinkRequest,
        context: grpc.ServicerContext,
    ) -> mod_pb2.GetModDownloadLinkResponse:
        return _get_mod_download_link(self._service, request, context)
    
    def ConfirmUpload(
        self,
        request: mod_pb2.ConfirmUploadRequest,
        context: grpc.ServicerContext,
    ) -> mod_pb2.ConfirmUploadResponse:
        return _confirm_upload(self._service, request, context)
