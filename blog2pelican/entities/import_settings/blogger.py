from dataclasses import dataclass
from typing import Literal

from .base import ImportSettings


@dataclass
class BloggerImportSettings(ImportSettings):
    origin: Literal["blogger"]

    """Put pages in pages subdirectories"""
    dirpage: bool  # Blogger & WordPress only
