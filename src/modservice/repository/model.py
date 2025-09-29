from dataclasses import dataclass


@dataclass
class Mod:
    title: str
    author_id: int
    filename: str
    description: str
