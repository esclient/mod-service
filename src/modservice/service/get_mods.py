from typing import Any

from modservice.repository.repository import ModRepository


def get_mods(
    repo: ModRepository,
) -> list[dict[str, Any]]:
    return repo.get_mods()
