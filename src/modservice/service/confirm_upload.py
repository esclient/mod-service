from modservice.repository.repository import ModRepository


def confirm_upload(repo: ModRepository, mod_id: int) -> bool:
    return repo.confirm_upload(mod_id)
