from dataclasses import dataclass
from typing import Literal

from .base import ImportSettings


@dataclass
class WordPressImportSettings(ImportSettings):
    origin: Literal["wordpress"]

    """Put pages in pages subdirectories"""
    dirpage: bool  # Blogger & WordPress only
