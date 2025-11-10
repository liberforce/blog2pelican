import sys
from dataclasses import dataclass

import pelican.utils
from pelican.settings import DEFAULT_CONFIG

from .base import BlogParser


class DotclearParser(BlogParser):
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

    def _dotclear_parse_post(self, post):
        fields = post.split('","')
        postobj = Post(
            # post_id = fields[0][1:],
            # blog_id = fields[1],
            # user_id = fields[2],
            cat_ids=fields[3],
            # post_dt = fields[4],
            # post_tz = fields[5],
            post_creadt=fields[6],
            # post_upddt = fields[7],
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
            # post_status = fields[20],
            # post_selected = fields[21],
            # post_position = fields[22],
            # post_open_comment = fields[23],
            # post_open_tb = fields[24],
            # nb_comment = fields[25],
            # nb_trackback = fields[26],
            post_meta=fields[27],
            # redirect_url = fields[28][:-1],
        )

        # remove seconds
        postobj.post_creadt = ":".join(postobj.post_creadt.split(":")[0:2])

        return postobj

    def parse(self, path: str):
        """Opens a Dotclear export file, and yield pelican fields"""
        try:
            from bs4 import BeautifulSoup  # noqa: PLC0415
        except ImportError:
            error = (
                "Missing dependency "
                '"BeautifulSoup4" and "lxml" required '
                "to import Dotclear files."
            )
            sys.exit(error)

        category_list, posts = self._dotclear_parse_sections(path)

        print(f"{len(posts)} posts read.")

        subs = DEFAULT_CONFIG["SLUG_REGEX_SUBSTITUTIONS"]
        for post in posts:
            postobj = self._dotclear_parse_post(post)

            author = ""
            categories = []
            tags = []

            if postobj.cat_ids:
                categories = [
                    category_list[cat_id].strip()
                    for cat_id in postobj.cat_ids.split(",")
                ]

            # Get tags related to a post
            tag = (
                postobj.post_meta.replace("{", "")
                .replace("}", "")
                .replace('a:1:s:3:\\"tag\\";a:', "")
                .replace("a:0:", "")
            )
            if len(tag) > 1:
                if len(tag[:1]) == 1:
                    newtag = tag.split('"')[1]
                    tags.append(
                        BeautifulSoup(newtag, "xml")
                        # bs4 always outputs UTF-8
                        .decode("utf-8")
                    )
                else:
                    i = 1
                    j = 1
                    while i <= int(tag[:1]):
                        newtag = tag.split('"')[j].replace("\\", "")
                        tags.append(
                            BeautifulSoup(newtag, "xml")
                            # bs4 always outputs UTF-8
                            .decode("utf-8")
                        )
                        i = i + 1
                        if j < int(tag[:1]) * 2:
                            j = j + 2

            """
            dotclear2 does not use markdown by default unless
            you use the markdown plugin
            Ref: http://plugins.dotaddict.org/dc2/details/formatting-markdown
            """
            if postobj.post_format == "markdown":
                content = postobj.post_excerpt + postobj.post_content
            else:
                content = postobj.post_excerpt_xhtml + postobj.post_content_xhtml
                content = content.replace("\\n", "")
                postobj.post_format = "html"

            kind = "article"  # TODO: Recognise pages
            status = "published"  # TODO: Find a way for draft posts

            yield (
                postobj.post_title,
                content,
                pelican.utils.slugify(postobj.post_title, regex_subs=subs),
                postobj.post_creadt,
                author,
                categories,
                tags,
                status,
                kind,
                postobj.post_format,
            )


@dataclass
class Post:
    cat_ids: list[str]
    post_creadt: str
    post_format: str
    post_title: str
    post_excerpt: str
    post_excerpt_xhtml: str
    post_content: str
    post_content_xhtml: str
    # post_notes: str
    # post_words: str
    # post_status: str
    # post_selected: str
    # post_position: str
    # post_open_comment: str
    # post_open_tb: str
    # nb_comment: str
    # nb_trackback: str
    post_meta: str
    # redirect_url: str
