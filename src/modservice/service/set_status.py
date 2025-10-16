from modservice.repository.repository import ModRepository


async def set_status(repo: ModRepository, mod_id: int, status: str) -> bool:
    return await repo.set_status(mod_id, status)
