import datetime
import json
import urllib.request as urllib_request
from collections.abc import Generator

from pelican.settings import DEFAULT_CONFIG
from pelican.utils import SafeDatetime, slugify

from blog2pelican.entities.import_settings import ImportSettings
from blog2pelican.entities.posts import PelicanPost

from .base import BlogParser


class TumblrParser(BlogParser):
    def __init__(self, settings: ImportSettings, blogname=None):
        super().__init__(settings)
        self.blogname = blogname

    def _get_tumblr_posts(self, api_key, offset=0):
        url = (
            f"https://api.tumblr.com/v2/blog/{self.blogname}.tumblr.com/"
            f"posts?api_key={api_key}&offset={offset}&filter=raw"
        )
        request = urllib_request.Request(url)
        handle = urllib_request.urlopen(request)
        posts = json.loads(handle.read().decode("utf-8"))
        return posts.get("response").get("posts")

    def parse(self, api_key) -> Generator[PelicanPost]:
        """Imports Tumblr posts (API v2)"""
        offset = 0
        posts = self._get_tumblr_posts(api_key, offset)
        subs = DEFAULT_CONFIG["SLUG_REGEX_SUBSTITUTIONS"]
        while len(posts) > 0:
            for post in posts:
                title = (
                    post.get("title")
                    or post.get("source_title")
                    or post.get("type").capitalize()
                )
                slug = post.get("slug") or slugify(title, regex_subs=subs)
                tags = post.get("tags")
                timestamp = post.get("timestamp")
                date = SafeDatetime.fromtimestamp(
                    int(timestamp), tz=datetime.timezone.utc
                ).strftime("%Y-%m-%d %H:%M:%S%z")
                slug = (
                    SafeDatetime.fromtimestamp(
                        int(timestamp), tz=datetime.timezone.utc
                    ).strftime("%Y-%m-%d-")
                    + slug
                )
                post_format = post.get("format")
                content = post.get("body")
                post_type = post.get("type")
                if post_type == "photo":
                    if post_format == "markdown":
                        fmtstr = "![%s](%s)"
                    else:
                        fmtstr = '<img alt="%s" src="%s" />'
                    content = "\n".join(
                        fmtstr
                        % (photo.get("caption"), photo.get("original_size").get("url"))
                        for photo in post.get("photos")
                    )
                elif post_type == "quote":
                    if post_format == "markdown":
                        fmtstr = "\n\n&mdash; %s"
                    else:
                        fmtstr = "<p>&mdash; %s</p>"
                    content = post.get("text") + fmtstr % post.get("source")
                elif post_type == "link":
                    if post_format == "markdown":
                        fmtstr = "[via](%s)\n\n"
                    else:
                        fmtstr = '<p><a href="%s">via</a></p>\n'
                    content = fmtstr % post.get("url") + post.get("description")
                elif post_type == "audio":
                    if post_format == "markdown":
                        fmtstr = "[via](%s)\n\n"
                    else:
                        fmtstr = '<p><a href="%s">via</a></p>\n'
                    content = (
                        fmtstr % post.get("source_url")
                        + post.get("caption")
                        + post.get("player")
                    )
                elif post_type == "video":
                    if post_format == "markdown":
                        fmtstr = "[via](%s)\n\n"
                    else:
                        fmtstr = '<p><a href="%s">via</a></p>\n'
                    source = fmtstr % post.get("source_url")
                    caption = post.get("caption")
                    players = [
                        # If embed_code is False, couldn't get the video
                        player.get("embed_code") or None
                        for player in post.get("player")
                    ]
                    # If there are no embeddable players, say so, once
                    if len(players) > 0 and all(player is None for player in players):
                        players = "<p>(This video isn't available anymore.)</p>\n"
                    else:
                        players = "\n".join(players)
                    content = source + caption + players
                elif post_type == "answer":
                    title = post.get("question")
                    content = (
                        "<p>"
                        '<a href="{}" rel="external nofollow">{}</a>'
                        ": {}"
                        "</p>\n"
                        " {}".format(
                            post.get("asking_name"),
                            post.get("asking_url"),
                            post.get("question"),
                            post.get("answer"),
                        )
                    )

                content = content.rstrip() + "\n"
                kind = "article"
                status = "published"  # TODO: Find a way for draft posts

                yield PelicanPost(
                    title,
                    content,
                    slug,
                    date,
                    post.get("blog_name"),
                    [post_type],
                    tags,
                    status,
                    kind,
                    post_format,
                )

            offset += len(posts)
            posts = self._get_tumblr_posts(api_key, offset)
