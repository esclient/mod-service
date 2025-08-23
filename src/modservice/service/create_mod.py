from modservice.repository.repository import ModRepository


def create_mod(
    repo: ModRepository, mod_title: str, author_id: int, filename: str, description: str
) -> int:
    return repo.create_mod(mod_title, author_id, filename, description)