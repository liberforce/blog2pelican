#!/usr/bin/env python
import argparse
import logging
import os
import sys

import pelican.log

from blog2pelican.domain.entities.settings import create_settings
from blog2pelican.domain.use_cases.convert_blog import create_blog_converter

logger = logging.getLogger(__name__)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transform feed, Blogger, Dotclear, Tumblr, or "
        "WordPress files into reST (rst) or Markdown (md) files. "
        "Be sure to have pandoc installed.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(dest="input", help="The input file to read")
    parser.add_argument(
        "--origin",
        choices=["blogger", "dotclear", "medium", "tumblr", "wordpress", "feed"],
        action="store",
        help="Origin of the file to import",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        default="content",
        help="Output path",
    )
    parser.add_argument(
        "-m",
        "--markup",
        choices=["rst", "markdown"],
        dest="markup",
        default="rst",
        help="Output markup format",
    )
    parser.add_argument(
        "--dir-cat",
        action="store_true",
        dest="dircat",
        help="Put files in directories with categories name",
    )
    parser.add_argument(
        "--dir-page",
        action="store_true",
        dest="dirpage",
        help=(
            'Put files recognised as pages in "pages/" sub-directory'
            " (blogger and wordpress import only)"
        ),
    )
    parser.add_argument(
        "--filter-author",
        dest="author",
        help="Import only post from the specified author",
    )
    parser.add_argument(
        "--strip-raw",
        action="store_true",
        dest="strip_raw",
        help="Strip raw HTML code that can't be converted to "
        "markup such as flash embeds or iframes (wordpress import only)",
    )
    parser.add_argument(
        "--wp-custpost",
        action="store_true",
        dest="wp_custpost",
        help="Put wordpress custom post types in directories. If used with "
        "--dir-cat option directories will be created as "
        "/post_type/category/ (wordpress import only)",
    )
    parser.add_argument(
        "--wp-attach",
        action="store_true",
        dest="wp_attach",
        help="(wordpress import only) Download files uploaded to wordpress as "
        "attachments. Files will be added to posts as a list in the post "
        "header. All files will be downloaded, even if "
        "they aren't associated with a post. Files will be downloaded "
        "with their original path inside the output directory. "
        "e.g. output/wp-uploads/date/postname/file.jpg "
        "-- Requires an internet connection --",
    )
    parser.add_argument(
        "--disable-slugs",
        action="store_true",
        dest="disable_slugs",
        help="Disable storing slugs from imported posts within output. "
        "With this disabled, your Pelican URLs may not be consistent "
        "with your original posts.",
    )
    parser.add_argument(
        "-b",
        "--blogname",
        dest="blogname",
        help="Blog name (Tumblr import only)",
    )
    return parser


def create_output_dir_if_required(dirname: str):
    if not os.path.exists(dirname):
        try:
            os.mkdir(dirname)
        except OSError:
            error = "Unable to create the output folder: " + dirname
            sys.exit(error)


def main():
    argument_parser = build_argument_parser()
    args = argument_parser.parse_args()
    settings = create_settings(args.origin, args)
    settings.check()

    # logging.setLoggerClass has to be called before logging.getLogger
    pelican.log.init()

    bc = create_blog_converter(settings.origin)
    posts = bc.extract_posts(settings)
    create_output_dir_if_required(settings.output)
    attachments = bc.extract_attachments(settings)
    bc.convert(posts, settings, args, attachments)


if __name__ == "__main__":
    main()
