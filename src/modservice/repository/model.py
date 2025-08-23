from dataclasses import dataclass


@dataclass
class Mod:
    mod_title: str
    author_id: int
    filename: str
    description: str
