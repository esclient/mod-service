import grpc

from modservice.grpc import mod_pb2, mod_pb2_grpc
from modservice.handler.create_mod import CreateMod as _create_mod
from modservice.handler.get_mod_download_link import (
    GetDownloadLink as _get_mod_download_link,
)
<<<<<<< HEAD
from modservice.handler.get_mods import GetMods as _get_mods
=======

# TODO: Раскомментировать когда Тимоха добавит GetMods в proto файл
# from modservice.handler.get_mods import GetMods as _get_mods
>>>>>>> bb6b9b7 (GetMods (без хендлера и пары потенциально нужных строчек в БД, жду Тимоху), убрал ругань на whitespace, чёт он на SQL запрос триггерится с ним)
from modservice.handler.set_status import SetStatus as _set_status
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

    def SetStatus(
        self,
        request: mod_pb2.SetStatusRequest,
        context: grpc.ServicerContext,
    ) -> mod_pb2.SetStatusResponse:
        return _set_status(self._service, request, context)

    def GetMods(
        self,
        request: mod_pb2.GetModsRequest,
        context: grpc.ServicerContext,
    ) -> mod_pb2.GetModsResponse:
        return _get_mods(self._service, request, context)
