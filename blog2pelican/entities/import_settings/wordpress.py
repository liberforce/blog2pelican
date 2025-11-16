from dataclasses import dataclass
from typing import Literal

from .base import ImportSettings


@dataclass
class WordPressImportSettings(ImportSettings):
    origin: Literal["wordpress"]

    """Put pages in pages subdirectories"""
    dirpage: bool  # Blogger & WordPress only

    """Put WordPress custom post types in directories."""
    custpost: bool

    """Download files uploaded to wordpress as attachments"""
    wp_attach: bool
