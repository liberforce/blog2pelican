import logging
import os
import pathlib
import sys
import tempfile
from collections import defaultdict
from collections.abc import Generator, Iterable
from typing import cast

from blog2pelican.adapters.blog_readers import create_blog_reader
from blog2pelican.app.use_cases.convert_post import (
    ConvertPostUseCase,
    download_attachments,
)
from blog2pelican.domain.entities.posts import Post
from blog2pelican.domain.entities.settings import Settings, WordPressSettings
from blog2pelican.domain.ports.blog_reader import BlogReader
from blog2pelican.helpers.pandoc import Pandoc
from blog2pelican.helpers.soup import soup_from_xml_file

logger = logging.getLogger(__name__)


class MissingPandocError(Exception):
    pass


def is_pandoc_needed(in_markup):
    return in_markup in ("html", "wp-html")


def get_filename(post_name, post_id):
    if post_name is None or post_name.isspace():
        return post_id
    else:
        return post_name


def create_output_dir_if_required(dirname: str | pathlib.Path):
    if not os.path.exists(dirname):
        try:
            os.mkdir(dirname)
        except OSError:
            error = f"Unable to create the output folder: {dirname}"
            sys.exit(error)


class ConvertBlogUseCase:
    def __init__(self):
        self.pandoc = Pandoc()

    def convert_blog(self, settings: Settings):
        posts = self.extract_posts(settings)
        create_output_dir_if_required(settings.output_dir)
        attachments = self.extract_attachments(settings)
        self.convert(posts, settings, attachments)

    def extract_posts(self, settings: Settings) -> Generator[Post]:
        blog_reader: BlogReader = create_blog_reader(settings.engine)
        blog_reader.use_settings(settings)
        return blog_reader.read_posts(settings.input)

    def convert_post(
        self,
        post: Post,
        settings: Settings,
        pandoc_tmpdir: str | None = None,
        strip_raw=False,
        dirpage=False,
        wp_custpost=False,
        wp_attach=False,
        attachments=None,
    ):
        if (
            settings.allowed_authors is not None
            and post.author not in settings.allowed_authors
        ):
            return

        if is_pandoc_needed(post.markup) and not self.pandoc.version:
            raise MissingPandocError

        pc = ConvertPostUseCase(pandoc=self.pandoc)
        pc.convert(
            post,
            settings,
            pandoc_tmpdir,
            strip_raw,
            dirpage,
            wp_custpost,
            wp_attach,
            attachments,
        )

        if wp_attach and attachments and None in attachments:
            print("downloading attachments that don't have a parent post")
            urls = attachments[None]
            download_attachments(settings.output_dir, urls)

    def extract_attachments(self, settings: Settings):
        """
        Return a dictionary of posts that have attachments.

        Each post has list of the attachment_urls.
        """
        if settings.engine != "wordpress":
            return None

        s = cast(WordPressSettings, settings)

        if not s.wp_attach:
            return None

        xml_filepath = settings.input
        soup = soup_from_xml_file(xml_filepath)
        items = soup.rss.channel.find_all("item")
        names = {}
        attachments = []

        for item in items:
            kind = item.find("post_type").string
            post_name = item.find("post_name").string
            post_id = item.find("post_id").string

            if kind == "attachment":
                attachments.append(
                    (
                        item.find("post_parent").string,
                        item.find("attachment_url").string,
                    )
                )
            else:
                filename = get_filename(post_name, post_id)
                names[post_id] = filename
        attachedposts = defaultdict(set)
        for parent, url in attachments:
            try:
                parent_name = names[parent]
            except KeyError:
                # attachment's parent is not a valid post
                parent_name = None

            attachedposts[parent_name].add(url)
        return attachedposts

    def convert(
        self,
        posts: Iterable[Post],
        settings: Settings,
        attachments,
    ):
        args = vars(settings)
        posts_require_pandoc = []
        with tempfile.TemporaryDirectory() as pandoc_tmpdir:
            for post in posts:
                try:
                    self.convert_post(
                        post,
                        settings,
                        pandoc_tmpdir,
                        dirpage=args.get("dirpage", False),
                        strip_raw=args.get("strip_raw", False),
                        wp_custpost=args.get("wp_custpost", False),
                        wp_attach=args.get("wp_attach", False),
                        attachments=attachments or None,
                    )
                except MissingPandocError:
                    posts_require_pandoc.append(post.filename)

        if posts_require_pandoc:
            logger.error(
                "Pandoc must be installed to import the following posts:\n  {}".format(
                    "\n  ".join(posts_require_pandoc)
                )
            )
