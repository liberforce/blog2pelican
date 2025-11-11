import logging
from dataclasses import dataclass

import pelican.utils
import phpserialize
from pelican.settings import DEFAULT_CONFIG

from blog2pelican.helpers.pelican_format import pelican_format_datetime

from .base import BlogParser

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


class DotclearParser(BlogParser):
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

    def _dotclear_parse_sections(self, file: str):
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

    def _dotclear_parse_post(self, post) -> DotclearPost:
        fields = post.strip('"').split('","')
        postobj = DotclearPost(
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

        return postobj

    def _adapt_content(self, content: str) -> str:
        # Unescape backquoted characters
        content = content.replace("\\n", "")
        content = content.replace("\\", "")
        return content

    def parse(self, path: str):
        """Opens a Dotclear export file, and yield pelican fields"""
        category_list, posts = self._dotclear_parse_sections(path)

        print(f"{len(posts)} posts read.")

        subs = DEFAULT_CONFIG["SLUG_REGEX_SUBSTITUTIONS"]
        for post in posts:
            postobj = self._dotclear_parse_post(post)

            author = postobj.user_id
            categories = []
            tags = self._get_tags(postobj.post_meta, postobj.post_title)

            if postobj.cat_ids:
                categories = [
                    category_list[cat_id].strip()
                    for cat_id in postobj.cat_ids.split(",")
                ]

            """
            dotclear2 does not use markdown by default unless
            you use the markdown plugin
            Ref: http://plugins.dotaddict.org/dc2/details/formatting-markdown
            """
            if postobj.post_format == "markdown":
                content = postobj.post_excerpt + postobj.post_content
            else:
                content = postobj.post_excerpt_xhtml + postobj.post_content_xhtml
                content = self._adapt_content(content)

                postobj.post_format = "html"

            kind = "article"  # TODO: Recognise pages
            status = "published"  # TODO: Find a way for draft posts

            yield (
                postobj.post_title,
                content,
                pelican.utils.slugify(postobj.post_title, regex_subs=subs),
                postobj.post_dt,
                author,
                categories,
                tags,
                status,
                kind,
                postobj.post_format,
            )
