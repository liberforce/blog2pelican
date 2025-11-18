from dataclasses import dataclass
from typing import Literal


@dataclass(kw_only=True)
class Settings:
    """
    Import Settings
    """

    """Origin of the blog to import"""
    origin: Literal[
        "blogger",
        "dotclear",
        "medium",
        "tumblr",
        "wordpress",
        "feed",
    ]

    """Input path to read blog data from"""
    input: str

    """Output path for generated imported files"""
    output: str  # FIXME: use type for files/dirs

    """Markup format to use in output"""
    markup: Literal["rst", "markdown"]

    """Author whose posts to import, or None to select all"""
    author: str | None

    """Put files in directories with categories name"""
    dircat: bool

    def check(self):
        """Check if the settings are consistent for the selected origin"""
