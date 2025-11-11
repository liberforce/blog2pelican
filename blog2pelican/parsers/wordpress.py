import logging
import re
from collections.abc import Generator
from html import unescape

from pelican.utils import SafeDatetime

from blog2pelican.entities.posts import PelicanPost
from blog2pelican.helpers.soup import soup_from_xml_file
from blog2pelican.tool import get_filename

from .base import BlogParser

logger = logging.getLogger(__name__)


class WordPressParser(BlogParser):
    def __init__(self, custpost: bool = False):
        self.custpost = custpost

    def decode_wp_content(sefl, content, br=True):
        pre_tags = {}
        if content is None or content.strip() == "":
            return ""

        content += "\n"
        if "<pre" in content:
            pre_parts = content.split("</pre>")
            last_pre = pre_parts.pop()
            content = ""
            pre_index = 0

            for pre_part in pre_parts:
                start = pre_part.find("<pre")
                if start == -1:
                    content = content + pre_part
                    continue
                name = f"<pre wp-pre-tag-{pre_index}></pre>"
                pre_tags[name] = pre_part[start:] + "</pre>"
                content = content + pre_part[0:start] + name
                pre_index += 1
            content = content + last_pre

        content = re.sub(r"<br />\s*<br />", "\n\n", content)
        allblocks = (
            "(?:table|thead|tfoot|caption|col|colgroup|tbody|tr|"
            "td|th|div|dl|dd|dt|ul|ol|li|pre|select|option|form|"
            "map|area|blockquote|address|math|style|p|h[1-6]|hr|"
            "fieldset|noscript|samp|legend|section|article|aside|"
            "hgroup|header|footer|nav|figure|figcaption|details|"
            "menu|summary)"
        )
        content = re.sub(r"(<" + allblocks + r"[^>]*>)", "\n\\1", content)
        content = re.sub(r"(</" + allblocks + r">)", "\\1\n\n", content)
        #    content = content.replace("\r\n", "\n")
        if "<object" in content:
            # no <p> inside object/embed
            content = re.sub(r"\s*<param([^>]*)>\s*", "<param\\1>", content)
            content = re.sub(r"\s*</embed>\s*", "</embed>", content)
            #    content = re.sub(r'/\n\n+/', '\n\n', content)
        pgraphs = filter(lambda s: s != "", re.split(r"\n\s*\n", content))
        content = ""
        for p in pgraphs:
            content = content + "<p>" + p.strip() + "</p>\n"
        # under certain strange conditions it could create
        # a P of entirely whitespace
        content = re.sub(r"<p>\s*</p>", "", content)
        content = re.sub(
            r"<p>([^<]+)</(div|address|form)>", "<p>\\1</p></\\2>", content
        )
        # don't wrap tags
        content = re.sub(r"<p>\s*(</?" + allblocks + r"[^>]*>)\s*</p>", "\\1", content)
        # problem with nested lists
        content = re.sub(r"<p>(<li.*)</p>", "\\1", content)
        content = re.sub(r"<p><blockquote([^>]*)>", "<blockquote\\1><p>", content)
        content = content.replace("</blockquote></p>", "</p></blockquote>")
        content = re.sub(r"<p>\s*(</?" + allblocks + "[^>]*>)", "\\1", content)
        content = re.sub(r"(</?" + allblocks + r"[^>]*>)\s*</p>", "\\1", content)
        if br:

            def _preserve_newline(match):
                return match.group(0).replace("\n", "<WPPreserveNewline />")

            content = re.sub(
                r"/<(script|style).*?<\/\\1>/s", _preserve_newline, content
            )
            # optionally make line breaks
            content = re.sub(r"(?<!<br />)\s*\n", "<br />\n", content)
            content = content.replace("<WPPreserveNewline />", "\n")
        content = re.sub(r"(</?" + allblocks + r"[^>]*>)\s*<br />", "\\1", content)
        content = re.sub(
            r"<br />(\s*</?(?:p|li|div|dl|dd|dt|th|pre|td|ul|ol)[^>]*>)", "\\1", content
        )
        content = re.sub(r"\n</p>", "</p>", content)

        if pre_tags:

            def _multi_replace(dic, string):
                pattern = r"|".join(map(re.escape, dic.keys()))
                return re.sub(pattern, lambda m: dic[m.group()], string)

            content = _multi_replace(pre_tags, content)

        # convert [caption] tags into <figure>
        content = re.sub(
            r"\[caption(?:.*?)(?:caption=\"(.*?)\")?\]"
            r"((?:\<a(?:.*?)\>)?(?:\<img.*?\>)(?:\<\/a\>)?)\s?(.*?)\[\/caption\]",
            r"<figure>\n\2\n<figcaption>\1\3</figcaption>\n</figure>",
            content,
        )

        return content

    def parse(self, xml) -> Generator[PelicanPost]:
        """Opens a wordpress XML file, and yield Pelican fields"""

        soup = soup_from_xml_file(xml)
        items = soup.rss.channel.find_all("item")
        for item in items:
            if item.find("status").string in ["publish", "draft"]:
                try:
                    # Use HTMLParser due to issues with BeautifulSoup 3
                    title = unescape(item.title.contents[0])
                except IndexError:
                    title = "No title [{}]".format(item.find("post_name").string)
                    logger.warning('Post "%s" is lacking a proper title', title)

                post_name = item.find("post_name").string
                post_id = item.find("post_id").string
                filename = get_filename(post_name, post_id)

                content = item.find("encoded").string
                raw_date = item.find("post_date").string
                if raw_date == "0000-00-00 00:00:00":
                    date = None
                else:
                    date_object = SafeDatetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S")
                    date = date_object.strftime("%Y-%m-%d %H:%M")
                author = item.find("creator").string

                categories = [
                    cat.string
                    for cat in item.find_all("category", {"domain": "category"})
                ]

                tags = [
                    tag.string
                    for tag in item.find_all("category", {"domain": "post_tag"})
                ]
                # To publish a post the status should be 'published'
                status = (
                    "published"
                    if item.find("status").string == "publish"
                    else item.find("status").string
                )

                kind = "article"
                post_type = item.find("post_type").string
                if post_type == "page":
                    kind = "page"
                elif self.custpost:
                    if post_type == "post":
                        pass
                    # Old behaviour was to name everything not a page as an
                    # article.Theoretically all attachments have status == inherit
                    # so no attachments should be here. But this statement is to
                    # maintain existing behaviour in case that doesn't hold true.
                    elif post_type == "attachment":
                        pass
                    else:
                        kind = post_type
                yield PelicanPost(
                    title,
                    content,
                    filename,
                    date,
                    author,
                    categories,
                    tags,
                    status,
                    kind,
                    "wp-html",
                )
