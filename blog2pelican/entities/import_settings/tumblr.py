from dataclasses import dataclass
from typing import Literal

from .base import ImportSettings


@dataclass
class TumblrImportSettings(ImportSettings):
    origin: Literal["tumblr"]

    """Blog name"""
    blogname: str | None  # Tumblr only
