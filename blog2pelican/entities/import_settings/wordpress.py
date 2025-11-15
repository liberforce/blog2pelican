import sys
from dataclasses import dataclass
from typing import Literal

from .base import ImportSettings


@dataclass
class WordPressImportSettings(ImportSettings):
    origin: Literal["wordpress"]

    """Put pages in pages subdirectories"""
    dirpage: bool  # Blogger & WordPress only

    def check(self):
        if self.wp_attach and self.origin != "wordpress":
            error = (
                "You must be importing a wordpress xml to use the --wp-attach option"
            )
            sys.exit(error)
