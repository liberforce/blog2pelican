from dataclasses import dataclass


@dataclass
class Post:
    title: str
    content: str
    filename: str
    date: str | None
    author: str | None
    categories: list[str] | None
    tags: list[str] | None
    status: str | None
    kind: str
    markup: str
