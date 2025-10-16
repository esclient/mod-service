from typing import Any

from modservice.repository.repository import ModRepository


async def get_mods(
    repo: ModRepository,
) -> list[dict[str, Any]]:
    return await repo.get_mods()
