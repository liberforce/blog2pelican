from typing import Any

from .base import BlogParser


def create_blog_parser(origin: str, args: Any) -> BlogParser:
    if origin == "blogger":
        from blog2pelican.parsers.blogger import BloggerParser

        return BloggerParser()
    elif origin == "dotclear":
        from blog2pelican.parsers.dotclear import DotclearParser

        return DotclearParser()
    elif origin == "medium":
        from blog2pelican.parsers.medium import MediumParser

        return MediumParser()
    elif origin == "tumblr":
        from blog2pelican.parsers.tumblr import TumblrParser

        return TumblrParser(blogname=args.blogname)
    elif origin == "wordpress":
        from blog2pelican.parsers.wordpress import WordPressParser

        return WordPressParser(custpost=args.wp_custpost)
    elif origin == "feed":
        from blog2pelican.parsers.feed import FeedParser

        return FeedParser()
    else:
        raise ValueError(f"Unhandled origin {origin}")
