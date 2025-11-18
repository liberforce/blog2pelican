import logging
from collections import defaultdict
from collections.abc import Generator
from typing import Any, Sequence, cast

from blog2pelican.entities.import_settings import (
    ImportSettings,
    WordPressImportSettings,
)
from blog2pelican.entities.posts import PelicanPost
from blog2pelican.helpers.pandoc import Pandoc
from blog2pelican.helpers.soup import soup_from_xml_file
from blog2pelican.parsers import create_blog_parser
from blog2pelican.parsers.base import BlogParser
from blog2pelican.posts.converters import PostConverter, download_attachments

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


class BlogConverter:
    def extract_posts(
        self,
        settings: ImportSettings,
    ) -> Generator[PelicanPost]:
        blog_parser: BlogParser = create_blog_parser(settings.origin)
        blog_parser.use_settings(settings)
        return blog_parser.parse(settings.input)

    def convert_post(
        self,
        post: PelicanPost,
        settings: ImportSettings,
        output_path,
        dircat=False,
        strip_raw=False,
        disable_slugs=False,
        dirpage=False,
        filter_author=None,
        wp_custpost=False,
        wp_attach=False,
        attachments=None,
    ):
        if filter_author and filter_author != post.author:
            return

        pandoc = Pandoc()
        if is_pandoc_needed(post.markup) and not pandoc.version:
            raise MissingPandocError

        pc = PostConverter()
        pc.convert(
            post,
            settings,
            output_path,
            dircat,
            strip_raw,
            disable_slugs,
            dirpage,
            filter_author,
            wp_custpost,
            wp_attach,
            attachments,
        )

        if wp_attach and attachments and None in attachments:
            print("downloading attachments that don't have a parent post")
            urls = attachments[None]
            download_attachments(output_path, urls)

    def extract_attachments(self, settings: ImportSettings):
        return None

    def convert(
        self,
        posts: Sequence[PelicanPost],
        settings: ImportSettings,
        args: Any,
        attachments,
    ):
        posts_require_pandoc = []

        for post in posts:
            try:
                self.convert_post(
                    post,
                    settings,
                    args.output,
                    dircat=args.dircat or False,
                    dirpage=args.dirpage or False,
                    strip_raw=args.strip_raw or False,
                    disable_slugs=args.disable_slugs or False,
                    filter_author=args.author,
                    wp_custpost=args.wp_custpost or False,
                    wp_attach=args.wp_attach or False,
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


class WordPressConverter(BlogConverter):
    def extract_attachments(self, settings: ImportSettings):
        """
        Return a dictionary of posts that have attachments.

        Each post has list of the attachment_urls.
        """
        s = cast(WordPressImportSettings, settings)

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


_converter_classes = {
    "wordpress": WordPressConverter,
}


def create_blog_converter(origin: str) -> BlogConverter:
    return _converter_classes.get(origin, BlogConverter)()
