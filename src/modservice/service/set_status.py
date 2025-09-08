from modservice.repository.repository import ModRepository


def set_status(repo: ModRepository, mod_id: int, status: str) -> bool:
    return repo.set_status(mod_id, status)


