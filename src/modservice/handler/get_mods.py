import grpc

from modservice.grpc import mod_pb2
from modservice.service.service import ModService


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
            status=mod_data["status"],
            created_at=(
                mod_data["created_at"] if mod_data.get("created_at") else None
            ),
            # TODO: Раскомментировать когда добавятся в БД и proto:
            # avatar_url=mod_data.get("avatar_url", ""),
            # download_count=mod_data.get("download_count", 0),
            # rating=mod_data.get("rating", 0.0),
            # tags=mod_data.get("tags", []),
            # updated_at=mod_data["updated_at"] if mod_data.get("updated_at") else None,
        )
        mods.append(mod)

    return mod_pb2.GetModsResponse(mods=mods)
