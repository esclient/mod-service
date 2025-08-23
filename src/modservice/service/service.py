from modservice.repository.model import Mod
from modservice.repository.repository import ModRepository
from modservice.service.create_mod import create_mod as _create_mod


class ModService:
    def __init__(self, repo: ModRepository):
        self._repo = repo
    
    def create_mod(self, mod_title: str, author_id: int, filename: str, description: str) -> int:
        return _create_mod(self._repo, mod_title, author_id, filename, description)