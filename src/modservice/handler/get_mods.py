import grpc

from modservice.constants import STATUS_BANNED, STATUS_HIDDEN, STATUS_UPLOADED
from modservice.grpc import mod_pb2
from modservice.service.service import ModService

STATUS_TO_PROTO: dict[str, mod_pb2.ModStatus] = {
    STATUS_UPLOADED: mod_pb2.ModStatus.MOD_STATUS_UPLOADED,
    STATUS_BANNED: mod_pb2.ModStatus.MOD_STATUS_BANNED,
    STATUS_HIDDEN: mod_pb2.ModStatus.MOD_STATUS_HIDDEN,
}


def GetMods(
    service: ModService,
    request: mod_pb2.GetModsRequest,  # noqa: ARG001
    context: grpc.ServicerContext,  # noqa: ARG001
) -> mod_pb2.GetModsResponse:
    mods_data = service.get_mods()

    mods = []
    for mod_data in mods_data:
        mod = mod_pb2.Mod(
            id=mod_data["id"],
            author_id=mod_data["author_id"],
            title=mod_data["title"],
            description=mod_data["description"],
            version=mod_data["version"],
            status=STATUS_TO_PROTO[mod_data["status"]],
            created_at=(
                mod_data["created_at"] if mod_data.get("created_at") else None
            ),
            # avatar_url=mod_data.get("avatar_url", ""),
            # download_count=mod_data.get("download_count", 0),
            # tags=mod_data.get("tags", []),
            # updated_at=mod_data["updated_at"] if mod_data.get("updated_at") else None,
        )
        mods.append(mod)

    return mod_pb2.GetModsResponse(mods=mods)
