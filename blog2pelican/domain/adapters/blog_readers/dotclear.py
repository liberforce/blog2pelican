import logging
from collections.abc import Generator
from dataclasses import dataclass

import pelican.utils
import phpserialize
from pelican.settings import DEFAULT_CONFIG

from blog2pelican.domain.entities.posts import Post
from blog2pelican.domain.entities.settings import DotclearSettings
from blog2pelican.domain.ports.blog_reader import BlogReader
from blog2pelican.helpers.pelican_format import pelican_format_datetime

logger = logging.getLogger(__name__)


@dataclass
class DotclearPost:
    # post_id: str
    # blog_id: str
    user_id: str
    cat_ids: list[str]
    post_dt: str
    # post_tz: str
    post_creadt: str
    # post_upddt: str
    # post_password: str
    # post_type: str
    post_format: str
    # post_url: str
    # post_lang: str
    post_title: str
    post_excerpt: str
    post_excerpt_xhtml: str
    post_content: str
    post_content_xhtml: str
    # post_notes: str
    # post_words: str
    post_meta: str
    # post_status: str
    # post_selected: str
    # post_open_comment: str
    # post_position: str
    # post_open_comment: str
    # post_open_tb: str
    # nb_comment: str
    # nb_trackback: str
    # post_position: str


class DotclearReader(BlogReader[DotclearSettings]):
    def _get_tags(self, post_meta, post_title=None):
        """
        Get tags related to a post
        """
        # Unclassified posts will get a special tag.
        # This will make it easier to find them afterwards.
        tags = ["Unclassified"]

        # First, unescape characters that were escaped to store the data in
        # the backup file in CSV-like format
        post_meta = post_meta.replace("\\", "")
        if not post_meta:
            logger.debug("post has no metadata: '%s'", post_title)
            return tags

        tags_dict = phpserialize.loads(post_meta.encode("utf-8"))

        if not tags_dict:
            logger.debug("post has really no tags: '%s'", post_title)
            return tags

        if b"tag" not in tags_dict:
            logger.debug("post has no tags: '%s'", post_title)
            return tags

        tags = [tag.decode("utf-8") for tag in tags_dict[b"tag"].values()]
        return tags

    def _parse_sections(self, file: str):
        in_cat = False
        in_post = False
        category_list = {}
        posts = []

        with open(file, encoding="utf-8") as f:
            for line in f:
                # remove final \n
                line = line[:-1]

                if line.startswith("[category"):
                    in_cat = True
                elif line.startswith("[post"):
                    in_post = True
                elif in_cat:
                    fields = line.strip('"').split('","')
                    if not line:
                        in_cat = False
                    else:
                        category_list[fields[0]] = fields[2]
                elif in_post:
                    if not line:
                        in_post = False
                        break
                    else:
                        posts.append(line)

        return category_list, posts

    def _parse_raw_post(self, raw_post) -> DotclearPost:
        fields = raw_post.strip('"').split('","')
        dc_post = DotclearPost(
            # post_id = fields[0][1:],
            # blog_id = fields[1],
            user_id=fields[2],
            cat_ids=fields[3],
            # post_dt
            post_dt=pelican_format_datetime(fields[4]),
            # post_tz = fields[5],
            post_creadt=pelican_format_datetime(fields[6]),
            # post_upddt = pelican_format_datetime(fields[7]),
            # post_password = fields[8],
            # post_type = fields[9],
            post_format=fields[10],
            # post_url = fields[11],
            # post_lang = fields[12],
            post_title=fields[13],
            post_excerpt=fields[14],
            post_excerpt_xhtml=fields[15],
            post_content=fields[16],
            post_content_xhtml=fields[17],
            # post_notes = fields[18],
            # post_words = fields[19],
            post_meta=fields[20],
            # post_status = fields[20],
            # post_selected = fields[21],
            # post_position = fields[22],
            # post_open_comment = fields[23],
            # post_open_tb = fields[24],
            # nb_comment = fields[25],
            # nb_trackback = fields[26],
            # redirect_url = fields[28][:-1],
        )

        return dc_post

    def _adapt_content(self, content: str) -> str:
        # Unescape backquoted characters
        content = content.replace("\\n", "")
        content = content.replace("\\", "")
        return content

    def read_posts(self, path: str) -> Generator[Post]:
        """Parse a Dotclear export file, and yield posts"""
        categories_dict, raw_posts = self._parse_sections(path)

        print(f"{len(raw_posts)} posts read.")

        subs = DEFAULT_CONFIG["SLUG_REGEX_SUBSTITUTIONS"]
        for raw_post in raw_posts:
            dc_post = self._parse_raw_post(raw_post)

            author = dc_post.user_id
            tags = self._get_tags(dc_post.post_meta, dc_post.post_title)
            categories = [
                categories_dict[cat_id].strip()
                for cat_id in dc_post.cat_ids.split(",")
                if dc_post.cat_ids
            ]

            """
            dotclear2 does not use markdown by default unless
            you use the markdown plugin
            Ref: http://plugins.dotaddict.org/dc2/details/formatting-markdown
            """
            if dc_post.post_format == "markdown":
                content = dc_post.post_excerpt + dc_post.post_content
            else:
                content = dc_post.post_excerpt_xhtml + dc_post.post_content_xhtml
                content = self._adapt_content(content)

                dc_post.post_format = "html"

            kind = "article"  # TODO: Recognise pages
            status = "published"  # TODO: Find a way for draft posts

            yield Post(
                dc_post.post_title,
                content,
                pelican.utils.slugify(dc_post.post_title, regex_subs=subs),
                dc_post.post_dt,
                author,
                categories,
                tags,
                status,
                kind,
                dc_post.post_format,
            )
