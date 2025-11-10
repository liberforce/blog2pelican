#!/usr/bin/env python
from typing import Any

import argparse
import logging
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from urllib.error import URLError
from urllib.parse import quote, urlparse, urlsplit, urlunsplit
from urllib.request import urlretrieve

from docutils.utils import column_width

# because logging.setLoggerClass has to be called before logging.getLogger
from pelican.log import init
from pelican.settings import DEFAULT_CONFIG
from pelican.utils import slugify
from blog2pelican.helpers.soup import file_to_soup

logger = logging.getLogger(__name__)


def get_filename(post_name, post_id):
    if post_name is None or post_name.isspace():
        return post_id
    else:
        return post_name


def build_header(
    title,
    date,
    author,
    categories,
    tags,
    slug,
    status=None,
    attachments=None,
):
    """Build a header from a list of fields"""

    header = "{}\n{}\n".format(title, "#" * column_width(title))
    if date:
        header += f":date: {date}\n"
    if author:
        header += f":author: {author}\n"
    if categories:
        header += ":category: {}\n".format(", ".join(categories))
    if tags:
        header += ":tags: {}\n".format(", ".join(tags))
    if slug:
        header += f":slug: {slug}\n"
    if status:
        header += f":status: {status}\n"
    if attachments:
        header += ":attachments: {}\n".format(", ".join(attachments))
    header += "\n"
    return header


def build_asciidoc_header(
    title,
    date,
    author,
    categories,
    tags,
    slug,
    status=None,
    attachments=None,
):
    """Build a header from a list of fields"""

    header = f"= {title}\n"
    if author:
        header += f"{author}\n"
        if date:
            header += f"{date}\n"
    if categories:
        header += ":category: {}\n".format(", ".join(categories))
    if tags:
        header += ":tags: {}\n".format(", ".join(tags))
    if slug:
        header += f":slug: {slug}\n"
    if status:
        header += f":status: {status}\n"
    if attachments:
        header += ":attachments: {}\n".format(", ".join(attachments))
    header += "\n"
    return header


def build_markdown_header(
    title,
    date,
    author,
    categories,
    tags,
    slug,
    status=None,
    attachments=None,
):
    """Build a header from a list of fields"""
    header = f"Title: {title}\n"
    if date:
        header += f"Date: {date}\n"
    if author:
        header += f"Author: {author}\n"
    if categories:
        header += "Category: {}\n".format(", ".join(categories))
    if tags:
        header += "Tags: {}\n".format(", ".join(tags))
    if slug:
        header += f"Slug: {slug}\n"
    if status:
        header += f"Status: {status}\n"
    if attachments:
        header += "Attachments: {}\n".format(", ".join(attachments))
    header += "\n"
    return header


def get_ext(out_markup, in_markup="html"):
    if out_markup == "asciidoc":
        ext = ".adoc"
    elif in_markup == "markdown" or out_markup == "markdown":
        ext = ".md"
    else:
        ext = ".rst"
    return ext


def get_out_filename(
    output_path,
    filename,
    ext,
    kind,
    dirpage,
    dircat,
    categories,
    wp_custpost,
    slug_subs,
):
    filename = os.path.basename(filename)

    # Enforce filename restrictions for various filesystems at once; see
    # https://en.wikipedia.org/wiki/Filename#Reserved_characters_and_words
    # we do not need to filter words because an extension will be appended
    filename = re.sub(r'[<>:"/\\|?*^% ]', "-", filename)  # invalid chars
    filename = filename.lstrip(".")  # should not start with a dot
    if not filename:
        filename = "_"
    filename = filename[:249]  # allow for 5 extra characters

    out_filename = os.path.join(output_path, filename + ext)
    # option to put page posts in pages/ subdirectory
    if dirpage and kind == "page":
        pages_dir = os.path.join(output_path, "pages")
        if not os.path.isdir(pages_dir):
            os.mkdir(pages_dir)
        out_filename = os.path.join(pages_dir, filename + ext)
    elif not dirpage and kind == "page":
        pass
    # option to put wp custom post types in directories with post type
    # names. Custom post types can also have categories so option to
    # create subdirectories with category names
    elif kind != "article":
        if wp_custpost:
            typename = slugify(kind, regex_subs=slug_subs)
        else:
            typename = ""
            kind = "article"
        if dircat and (len(categories) > 0):
            catname = slugify(categories[0], regex_subs=slug_subs, preserve_case=True)
        else:
            catname = ""
        out_filename = os.path.join(output_path, typename, catname, filename + ext)
        if not os.path.isdir(os.path.join(output_path, typename, catname)):
            os.makedirs(os.path.join(output_path, typename, catname))
    # option to put files in directories with categories names
    elif dircat and (len(categories) > 0):
        catname = slugify(categories[0], regex_subs=slug_subs, preserve_case=True)
        out_filename = os.path.join(output_path, catname, filename + ext)
        if not os.path.isdir(os.path.join(output_path, catname)):
            os.mkdir(os.path.join(output_path, catname))

    return out_filename


def get_attachments(xml):
    """returns a dictionary of posts that have attachments with a list
    of the attachment_urls
    """
    soup = file_to_soup(xml)
    items = soup.rss.channel.find_all("item")
    names = {}
    attachments = []

    for item in items:
        kind = item.find("post_type").string
        post_name = item.find("post_name").string
        post_id = item.find("post_id").string

        if kind == "attachment":
            attachments.append(
                (item.find("post_parent").string, item.find("attachment_url").string)
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


def download_attachments(output_path, urls):
    """Downloads WordPress attachments and returns a list of paths to
    attachments that can be associated with a post (relative path to output
    directory). Files that fail to download, will not be added to posts"""
    locations = {}
    for url in urls:
        path = urlparse(url).path
        # teardown path and rebuild to negate any errors with
        # os.path.join and leading /'s
        path = path.split("/")
        filename = path.pop(-1)
        localpath = ""
        for item in path:
            if sys.platform != "win32" or ":" not in item:
                localpath = os.path.join(localpath, item)
        full_path = os.path.join(output_path, localpath)

        # Generate percent-encoded URL
        scheme, netloc, path, query, fragment = urlsplit(url)
        if scheme != "file":
            path = quote(path)
            url = urlunsplit((scheme, netloc, path, query, fragment))

        if not os.path.exists(full_path):
            os.makedirs(full_path)
        print(f"downloading {filename}")
        try:
            urlretrieve(url, os.path.join(full_path, filename))
            locations[url] = os.path.join(localpath, filename)
        except (URLError, OSError) as e:
            # Python 2.7 throws an IOError rather Than URLError
            logger.warning("No file could be downloaded from %s\n%s", url, e)
    return locations


def is_pandoc_needed(in_markup):
    return in_markup in ("html", "wp-html")


def get_pandoc_version():
    cmd = ["pandoc", "--version"]
    try:
        output = subprocess.check_output(cmd, text=True)
    except (subprocess.CalledProcessError, OSError) as e:
        logger.warning("Pandoc version unknown: %s", e)
        return ()

    return tuple(int(i) for i in output.split()[1].split("."))


def update_links_to_attached_files(content, attachments):
    for old_url, new_path in attachments.items():
        # url may occur both with http:// and https://
        http_url = old_url.replace("https://", "http://")
        https_url = old_url.replace("http://", "https://")
        for url in [http_url, https_url]:
            content = content.replace(url, "{static}" + new_path)
    return content


def fields2pelican(
    fields,
    out_markup,
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
    pandoc_version = get_pandoc_version()
    posts_require_pandoc = []

    slug_subs = DEFAULT_CONFIG["SLUG_REGEX_SUBSTITUTIONS"]

    for (
        title,
        content,
        filename,
        date,
        author,
        categories,
        tags,
        status,
        kind,
        in_markup,
    ) in fields:
        if filter_author and filter_author != author:
            continue
        if is_pandoc_needed(in_markup) and not pandoc_version:
            posts_require_pandoc.append(filename)

        slug = (not disable_slugs and filename) or None
        assert slug is None or filename == os.path.basename(
            filename
        ), f"filename is not a basename: {filename}"

        if wp_attach and attachments:
            try:
                urls = attachments[filename]
                links = download_attachments(output_path, urls)
            except KeyError:
                links = None
        else:
            links = None

        ext = get_ext(out_markup, in_markup)
        if ext == ".adoc":
            header = build_asciidoc_header(
                title,
                date,
                author,
                categories,
                tags,
                slug,
                status,
                attachments,
            )
        elif ext == ".md":
            header = build_markdown_header(
                title,
                date,
                author,
                categories,
                tags,
                slug,
                status,
                links.values() if links else None,
            )
        else:
            out_markup = "rst"
            header = build_header(
                title,
                date,
                author,
                categories,
                tags,
                slug,
                status,
                links.values() if links else None,
            )

        out_filename = get_out_filename(
            output_path,
            filename,
            ext,
            kind,
            dirpage,
            dircat,
            categories,
            wp_custpost,
            slug_subs,
        )
        print(out_filename)

        if in_markup in ("html", "wp-html"):
            with tempfile.TemporaryDirectory() as tmpdir:
                html_filename = os.path.join(tmpdir, "pandoc-input.html")
                # Replace newlines with paragraphs wrapped with <p> so
                # HTML is valid before conversion
                if in_markup == "wp-html":
                    from blog2pelican.parsers.wordpress import decode_wp_content

                    new_content = decode_wp_content(content)
                else:
                    paragraphs = content.splitlines()
                    paragraphs = [f"<p>{p}</p>" for p in paragraphs]
                    new_content = "".join(paragraphs)
                with open(html_filename, "w", encoding="utf-8") as fp:
                    fp.write(new_content)

                if pandoc_version < (2,):
                    parse_raw = "--parse-raw" if not strip_raw else ""
                    wrap_none = (
                        "--wrap=none" if pandoc_version >= (1, 16) else "--no-wrap"
                    )
                    cmd = (
                        'pandoc --normalize {0} --from=html --to={1} {2} -o "{3}" "{4}"'
                    )
                    cmd = cmd.format(
                        parse_raw,
                        out_markup if out_markup != "markdown" else "gfm",
                        wrap_none,
                        out_filename,
                        html_filename,
                    )
                else:
                    from_arg = "-f html+raw_html" if not strip_raw else "-f html"
                    cmd = 'pandoc {0} --to={1}-smart --wrap=none -o "{2}" "{3}"'
                    cmd = cmd.format(
                        from_arg,
                        out_markup if out_markup != "markdown" else "gfm",
                        out_filename,
                        html_filename,
                    )

                try:
                    rc = subprocess.call(cmd, shell=True)
                    if rc < 0:
                        error = f"Child was terminated by signal {-rc}"
                        sys.exit(error)

                    elif rc > 0:
                        error = "Please, check your Pandoc installation."
                        sys.exit(error)
                except OSError as e:
                    error = f"Pandoc execution failed: {e}"
                    sys.exit(error)

            with open(out_filename, encoding="utf-8") as fs:
                content = fs.read()
                if out_markup == "markdown":
                    # In markdown, to insert a <br />, end a line with two
                    # or more spaces & then a end-of-line
                    content = content.replace("\\\n ", "  \n")
                    content = content.replace("\\\n", "  \n")

            if wp_attach and links:
                content = update_links_to_attached_files(content, links)

        with open(out_filename, "w", encoding="utf-8") as fs:
            fs.write(header + content)

    if posts_require_pandoc:
        logger.error(
            "Pandoc must be installed to import the following posts:\n  {}".format(
                "\n  ".join(posts_require_pandoc)
            )
        )

    if wp_attach and attachments and None in attachments:
        print("downloading attachments that don't have a parent post")
        urls = attachments[None]
        download_attachments(output_path, urls)


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
        dest="markup",
        default="rst",
        help="Output markup format (supports rst & markdown)",
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
        "-b", "--blogname", dest="blogname", help="Blog name (Tumblr import only)"
    )
    return parser


def fields_from_input_type(input_type: str, args) -> tuple[Any]:
    if input_type == "blogger":
        from blog2pelican.parsers.blogger import blogger2fields

        fields = blogger2fields(args.input)
    elif input_type == "dotclear":
        from blog2pelican.parsers.dotclear import dotclear2fields

        fields = dotclear2fields(args.input)
    elif input_type == "medium":
        from blog2pelican.parsers.medium import mediumposts2fields

        fields = mediumposts2fields(args.input)
    elif input_type == "tumblr":
        from blog2pelican.parsers.tumblr import tumblr2fields

        fields = tumblr2fields(args.input, args.blogname)
    elif input_type == "wordpress":
        from blog2pelican.parsers.wordpress import wp2fields

        fields = wp2fields(args.input, args.wp_custpost or False)
    elif input_type == "feed":
        from blog2pelican.parsers.feed import feed2fields

        fields = feed2fields(args.input)
    else:
        raise ValueError(f"Unhandled input_type {input_type}")

    return fields


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
    input_type = args.origin
    fields = fields_from_input_type(input_type, args)
    create_output_dir_if_required(args.output)

    if args.wp_attach and input_type != "wordpress":
        error = "You must be importing a wordpress xml to use the --wp-attach option"
        sys.exit(error)

    if args.wp_attach:
        attachments = get_attachments(args.input)
    else:
        attachments = None

    # init logging
    init()
    fields2pelican(
        fields,
        args.markup,
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


if __name__ == "__main__":
    main()
