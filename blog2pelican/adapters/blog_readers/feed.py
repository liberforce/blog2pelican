import time
from collections.abc import Generator
from typing import cast

from pelican.settings import DEFAULT_CONFIG
from pelican.utils import slugify

from blog2pelican.domain.entities.posts import Post
from blog2pelican.domain.entities.settings import FeedSettings
from blog2pelican.domain.ports.blog_reader import BlogReader


class FeedReader(BlogReader[FeedSettings]):
    def read_posts(self, file) -> Generator[Post]:
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

            slug = slugify(entry.title, regex_subs=cast(list, subs))
            kind = "article"
            yield Post(
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
