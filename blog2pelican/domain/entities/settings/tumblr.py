from dataclasses import dataclass
from typing import Literal

from .base import Settings


@dataclass
class TumblrSettings(Settings):
    engine: Literal["tumblr"]

    """Blog name"""
    blogname: str | None  # Tumblr only
