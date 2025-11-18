from dataclasses import dataclass
from typing import Literal

from .base import Settings


@dataclass
class BloggerSettings(Settings):
    origin: Literal["blogger"]

    """Put pages in pages subdirectories"""
    dirpage: bool  # Blogger & WordPress only
