import os
import re
from collections.abc import Generator

import dateutil.parser

from blog2pelican.entities.import_settings import MediumImportSettings
from blog2pelican.entities.posts import PelicanPost
from blog2pelican.helpers.soup import import_bs4, soup_from_xml_file

from .base import BlogParser


class MediumParser(BlogParser[MediumImportSettings]):
    def strip_medium_post_content(self, soup) -> str:
        """Strip some tags and attributes from medium post content.

        For example, the 'section' and 'div' tags cause trouble while rendering.

        The problem with these tags is you can get a section divider (--------------)
        that is not between two pieces of content.  For example:

          Some text.

          .. container:: section-divider

             --------------

          .. container:: section-content

          More content.

        In this case, pandoc complains: "Unexpected section title or transition."

        Also, the "id" and "name" attributes in tags cause similar problems.  They show
        up in .rst as extra junk that separates transitions.
        """
        # Remove tags
        # section and div cause problems
        # footer also can cause problems, and has nothing we want to keep
        # See https://stackoverflow.com/a/8439761
        invalid_tags = ["section", "div", "footer"]
        for tag in invalid_tags:
            for match in soup.find_all(tag):
                match.unwrap()

        # Remove attributes
        # See https://stackoverflow.com/a/9045719
        invalid_attributes = ["name", "id", "class"]
        bs4 = import_bs4()
        for tag in soup.descendants:
            if isinstance(tag, bs4.element.Tag):
                tag.attrs = {
                    key: value
                    for key, value in tag.attrs.items()
                    if key not in invalid_attributes
                }

        # Get the string of all content, keeping other tags
        all_content = "".join(str(element) for element in soup.contents)
        return all_content

    def _medium2fields(self, filepath: str) -> PelicanPost:
        """Take an HTML post from a medium export, return Pelican posts."""

        soup = soup_from_xml_file(filepath, "html.parser")
        if not soup:
            raise ValueError(f"{filepath} could not be parsed by beautifulsoup")
        kind = "article"

        content = soup.find("section", class_="e-content")
        if not content:
            raise ValueError(f"{filepath}: Post has no content")

        title = soup.find("title").string or ""

        raw_date = soup.find("time", class_="dt-published")
        date = None
        if raw_date:
            # This datetime can include timezone, e.g., "2017-04-21T17:11:55.799Z"
            # python before 3.11 can't parse the timezone using datetime.fromisoformat
            # See also https://docs.python.org/3.10/library/datetime.html#datetime.datetime.fromisoformat
            # "This does not support parsing arbitrary ISO 8601 strings"
            # So, we use dateutil.parser, which can handle it.
            date_object = dateutil.parser.parse(raw_date.attrs["datetime"])
            date = date_object.strftime("%Y-%m-%d %H:%M")
            status = "published"
        else:
            status = "draft"
        author = soup.find("a", class_="p-author h-card")
        if author:
            author = author.string

        # Now that we're done with classes, we can strip the content
        content = self.strip_medium_post_content(content)

        # medium HTML export doesn't have tag or category
        # RSS feed has tags, but it doesn't have all the posts.
        tags = ()

        slug = self.medium_slug(filepath)

        return PelicanPost(
            title,
            content,
            slug,
            date,
            author,
            None,
            tags,
            status,
            kind,
            "html",
        )

    def medium_slug(self, filepath: str) -> str:
        """Make the filepath of a medium exported file into a slug."""
        # slug: filename without extension
        slug = os.path.basename(filepath)
        slug = os.path.splitext(slug)[0]
        # A medium export filename looks like date_-title-...html
        # But, RST doesn't like "_-" (see https://github.com/sphinx-doc/sphinx/issues/4350)
        # so get rid of it
        slug = slug.replace("_-", "-")
        # drop the hex string medium puts on the end of the filename, why keep it.
        # e.g., "-a8a8a8a8" or "---a9a9a9a9"
        # also: drafts don't need "--DRAFT"
        slug = re.sub(r"((-)+([0-9a-f]+|DRAFT))+$", "", slug)
        return slug

    def parse(self, path: str) -> Generator[PelicanPost]:
        """
        Take HTML posts in a medium export directory, and yield Pelican fields.
        path: path to the medium export dir, or file to parse.
        """
        for file in os.listdir(path):
            filename = os.fsdecode(file)
            yield self._medium2fields(os.path.join(path, filename))
