from dataclasses import dataclass
from typing import Literal

from .base import Settings


@dataclass
class TumblrSettings(Settings):
    origin: Literal["tumblr"]

    """Blog name"""
    blogname: str | None  # Tumblr only
