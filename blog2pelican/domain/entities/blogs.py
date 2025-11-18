from dataclasses import dataclass
from typing import Literal

from .posts import Post


@dataclass
class Blog:
    engine: Literal[
        "blogger",
        "dotclear",
        "feed",
        "medium",
        "pelican",
        "tumblr",
        "wordpress",
    ]
    posts: list[Post]
    authors: list[str]
