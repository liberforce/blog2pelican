import logging
import os.path
import subprocess
import sys

from blog2pelican.domain.entities.posts import PelicanPost

logger = logging.getLogger(__name__)


class Pandoc:
    def __init__(self, *args, **kwargs):
        self._version = None
        self.name = "Pandoc"

    def _get_version(self):
        version = ()

        cmd = ["pandoc", "--version"]
        try:
            output = subprocess.check_output(cmd, encoding="utf-8")
            version = tuple(int(i) for i in output.split()[1].split("."))
        except FileNotFoundError:
            logger.warning(
                "Pandoc not found, please check it is installed and in your PATH."
            )
        except (subprocess.CalledProcessError, OSError, ValueError) as e:
            logger.warning("Pandoc version unknown: %s", e)

        return version

    @property
    def version(self):
        if self._version is None:
            self._version = self._get_version()

        return self._version

    @property
    def available(self):
        return bool(self.version)

    def supports(self, input_format):
        return input_format in ("html", "wp-html")

    def convert(
        self,
        post: PelicanPost,
        out_markup,
        output_path,
        strip_raw,
        wp_attach,
        links,
        out_filename,
    ):
        """
        Convert text from one markup language to another.
        """
        if not self.supports(post.markup):
            return

        html_filename = os.path.join(output_path, post.filename + ".html")
        content = post.content

        with open(html_filename, "w", encoding="utf-8") as fp:
            # Replace newlines with paragraphs wrapped with <p> so
            # HTML is valid before conversion
            if post.markup == "wp-html":
                from blog2pelican.domain.adapters.blog_readers.wordpress import (
                    WordPressReader,
                )

                new_content = WordPressReader.decode_wp_content(content)
            else:
                paragraphs = content.splitlines()
                paragraphs = [f"<p>{p}</p>" for p in paragraphs]
                new_content = "".join(paragraphs)

            fp.write(new_content)

        if self.version < (2,):
            parse_raw = "--parse-raw" if not strip_raw else ""
            wrap_none = "--wrap=none" if self.version >= (1, 16) else "--no-wrap"
            cmd = 'pandoc --normalize {0} --from=html --to={1} {2} -o "{3}" "{4}"'
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

        os.remove(html_filename)

        with open(out_filename, "r", encoding="utf-8") as fs:
            content = fs.read()
            if out_markup == "markdown":
                # In markdown, to insert a <br />, end a line with two
                # or more spaces & then a end-of-line
                content = content.replace("\\\n ", "  \n")
                content = content.replace("\\\n", "  \n")

        if wp_attach and links:
            content = self.update_links_to_attached_files(content, links)

        return content

    def update_links_to_attached_files(self, content, attachments):
        for old_url, new_path in attachments.items():
            # url may occur both with http:// and https://
            http_url = old_url.replace("https://", "http://")
            https_url = old_url.replace("http://", "https://")
            for url in [http_url, https_url]:
                content = content.replace(url, "{static}" + new_path)
        return content
