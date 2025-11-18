from dataclasses import dataclass


@dataclass
class PelicanPost:
    title: str
    content: str
    filename: str
    date: str
    author: str
    categories: list[str]
    tags: list[str]
    status: str
    kind: str
    markup: str
