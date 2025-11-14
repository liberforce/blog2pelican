import dataclasses
from typing import Any, Mapping

from .base import ImportSettings
from .blogger import BloggerImportSettings
from .dotclear import DotclearImportSettings
from .feed import FeedImportSettings
from .medium import MediumImportSettings
from .tumblr import TumblrImportSettings
from .wordpress import WordPressImportSettings

_class_map = {
    "blogger": BloggerImportSettings,
    "dotclear": DotclearImportSettings,
    "medium": MediumImportSettings,
    "tumblr": TumblrImportSettings,
    "wordpress": WordPressImportSettings,
    "feed": FeedImportSettings,
}


def create_import_settings(origin: str, args: Mapping[str, Any]):
    """Factory to create the right set of options for chosen blog type."""
    cls = _class_map.get(origin, ImportSettings)
    fields = [f.name for f in dataclasses.fields(cls)]
    allowed = {k: v for k, v in vars(args).items() if k in fields}
    return cls(**allowed)
