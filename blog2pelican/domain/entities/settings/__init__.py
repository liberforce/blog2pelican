import dataclasses
from typing import Any, Mapping

from .base import Settings
from .blogger import BloggerSettings
from .dotclear import DotclearSettings
from .feed import FeedSettings
from .medium import MediumSettings
from .tumblr import TumblrSettings
from .wordpress import WordPressSettings

_class_map = {
    "blogger": BloggerSettings,
    "dotclear": DotclearSettings,
    "medium": MediumSettings,
    "tumblr": TumblrSettings,
    "wordpress": WordPressSettings,
    "feed": FeedSettings,
}


def create_settings(args: Mapping[str, Any]):
    """Factory to create the right set of options for chosen blog type."""
    cls = _class_map.get(args["engine"], Settings)
    fields = [f.name for f in dataclasses.fields(cls)]
    allowed = {k: v for k, v in args.items() if k in fields}
    return cls(**allowed)
