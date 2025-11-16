from typing import Any

from blog2pelican.entities.import_settings import ImportSettings

from .base import BlogParser


def create_blog_parser(origin: str, args: Any, settings: ImportSettings) -> BlogParser:
    if origin == "blogger":
        from blog2pelican.parsers.blogger import BloggerParser

        return BloggerParser(settings)
    elif origin == "dotclear":
        from blog2pelican.parsers.dotclear import DotclearParser

        return DotclearParser(settings)
    elif origin == "medium":
        from blog2pelican.parsers.medium import MediumParser

        return MediumParser(settings)
    elif origin == "tumblr":
        from blog2pelican.parsers.tumblr import TumblrParser

        return TumblrParser(settings, blogname=args.blogname)
    elif origin == "wordpress":
        from blog2pelican.parsers.wordpress import WordPressParser

        return WordPressParser(settings, custpost=args.wp_custpost)
    elif origin == "feed":
        from blog2pelican.parsers.feed import FeedParser

        return FeedParser(settings)
    else:
        raise ValueError(f"Unhandled origin {origin}")
