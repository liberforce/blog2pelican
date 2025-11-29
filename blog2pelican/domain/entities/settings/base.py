import pathlib
from dataclasses import dataclass
from typing import Literal


@dataclass(kw_only=True)
class Settings:
    """
    Import Settings
    """

    """Origin of the blog to import"""
    engine: Literal[
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
    output_dir: pathlib.Path

    """Markup format to use in output"""
    markup: Literal["rst", "markdown"]

    """Author whose posts to import, or None to select all"""
    allowed_authors: list[str] | None

    """Put files in directories with categories name"""
    dircat: bool

    """ Disable storing slugs from imported posts within output"""
    disable_slugs: bool = False

    def check(self):
        """Check if the settings are consistent for the selected engine"""
