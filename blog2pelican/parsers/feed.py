import time
from collections.abc import Generator

from pelican.settings import DEFAULT_CONFIG
from pelican.utils import slugify

from blog2pelican.entities.posts import PelicanPost

from .base import BlogParser


class FeedParser(BlogParser):
    def parse(self, file) -> Generator[PelicanPost]:
        """Read a feed and yield pelican fields"""
        import feedparser  # noqa: PLC0415

        d = feedparser.parse(file)
        subs = DEFAULT_CONFIG["SLUG_REGEX_SUBSTITUTIONS"]
        for entry in d.entries:
            date = (
                time.strftime("%Y-%m-%d %H:%M", entry.updated_parsed)
                if hasattr(entry, "updated_parsed")
                else None
            )
            author = entry.author if hasattr(entry, "author") else None
            tags = [e["term"] for e in entry.tags] if hasattr(entry, "tags") else None

            slug = slugify(entry.title, regex_subs=subs)
            kind = "article"
            yield PelicanPost(
                entry.title,
                entry.description,
                slug,
                date,
                author,
                [],
                tags,
                None,
                kind,
                "html",
            )
