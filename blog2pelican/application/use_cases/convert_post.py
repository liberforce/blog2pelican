import logging
import os.path
import re
import sys
from urllib.error import URLError
from urllib.parse import quote, urlparse, urlsplit, urlunsplit
from urllib.request import urlretrieve

from docutils.utils import column_width
from pelican.settings import DEFAULT_CONFIG
from pelican.utils import slugify

from blog2pelican.domain.entities.posts import Post
from blog2pelican.domain.entities.settings import Settings
from blog2pelican.helpers.pandoc import Pandoc

logger = logging.getLogger(__name__)


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


def download_attachments(output_path: str, urls: list[str]) -> dict[str, str]:
    """Downloads WordPress attachments and returns a list of paths to
    attachments that can be associated with a post (relative path to output
    directory). Files that fail to download, will not be added to posts"""
    locations = {}
    for url in urls:
        path = urlparse(url).path
        # teardown path and rebuild to negate any errors with
        # os.path.join and leading /'s
        path_components = path.split("/")
        filename = path_components.pop(-1)
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


def get_output_data(
    settings: Settings,
    post: Post,
    slug,
    attachments,
    links,
    output_path,
    dirpage,
    wp_custpost,
):
    slug_subs = DEFAULT_CONFIG["SLUG_REGEX_SUBSTITUTIONS"]
    out_markup = settings.markup
    ext = get_ext(settings.markup, post.markup)

    if ext == ".adoc":
        header = build_asciidoc_header(
            post.title,
            post.date,
            post.author,
            post.categories,
            post.tags,
            slug,
            post.status,
            attachments,
        )
    elif ext == ".md":
        header = build_markdown_header(
            post.title,
            post.date,
            post.author,
            post.categories,
            post.tags,
            slug,
            post.status,
            links.values() if links else None,
        )
    else:
        header = build_header(
            post.title,
            post.date,
            post.author,
            post.categories,
            post.tags,
            slug,
            post.status,
            links.values() if links else None,
        )

    out_filename = get_out_filename(
        output_path,
        post.filename,
        ext,
        post.kind,
        dirpage,
        settings.dircat,
        post.categories,
        wp_custpost,
        slug_subs,
    )
    return out_filename, out_markup, header


class ConvertPostUseCase:
    def __init__(self, pandoc=None):
        self.pandoc = Pandoc() if pandoc is None else pandoc

    def convert(
        self,
        post: Post,
        settings: Settings,
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
        slug = (not disable_slugs and post.filename) or None
        assert slug is None or post.filename == os.path.basename(
            post.filename
        ), f"filename is not a basename: {post.filename}"

        if wp_attach and attachments:
            try:
                urls = attachments[post.filename]
                links = download_attachments(output_path, urls)
            except KeyError:
                links = None
        else:
            links = None

        out_filename, out_markup, header = get_output_data(
            settings,
            post,
            slug,
            attachments,
            links,
            output_path,
            dirpage,
            wp_custpost,
        )
        print(out_filename)

        # Convert content
        if post.markup in ("html", "wp-html"):
            post.content = self.pandoc.convert(
                post,
                out_markup,
                strip_raw,
                wp_attach,
                links,
                out_filename,
            )
            post.markup = out_markup

        with open(out_filename, "w", encoding="utf-8") as fs:
            fs.write(header + post.content)
