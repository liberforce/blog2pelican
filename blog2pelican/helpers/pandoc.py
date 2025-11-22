import logging
import os.path
import subprocess
import sys
import tempfile

from blog2pelican.domain.entities.posts import Post

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

    def _wrap_into_html(self, post: Post) -> str:
        # Replace newlines with paragraphs wrapped with <p> so
        # HTML is valid before conversion
        if post.markup == "wp-html":
            from blog2pelican.adapters.blog_readers.wordpress import (
                WordPressReader,
            )

            html_content = WordPressReader.decode_wp_content(post.content)
        else:
            paragraphs = post.content.splitlines()
            paragraphs = [f"<p>{p}</p>" for p in paragraphs]
            html_content = "".join(paragraphs)

        return html_content

    def _build_legacy_pandoc_cmd(
        self,
        out_markup: str,
        strip_raw: bool,
        out_filename: str,
        html_filename: str,
    ):
        cmd = [
            "pandoc",
            "--normalize",
            "--parse-raw" if not strip_raw else "",
            "--from",
            "html",
            "--to",
            out_markup if out_markup != "markdown" else "gfm",
            "--wrap=none" if self.version >= (1, 16) else "--no-wrap",
            "--output",
            out_filename,
            html_filename,
        ]

        return cmd

    def _build_modern_pandoc_cmd(
        self,
        out_markup: str,
        strip_raw: bool,
        out_filename: str,
        html_filename: str,
    ):
        cmd = [
            "pandoc",
            "--from",
            "html+raw_html" if not strip_raw else "html",
            "--to",
            (out_markup if out_markup != "markdown" else "gfm") + "-smart",
            "--wrap",
            "none",
            "--output",
            out_filename,
            html_filename,
        ]
        return cmd

    def _build_pandoc_cmd(
        self,
        out_markup: str,
        strip_raw: bool,
        out_filename: str,
        html_filename: str,
    ) -> str:
        if self.version < (2,):
            build_pandoc_cmd = self._build_legacy_pandoc_cmd
        else:
            build_pandoc_cmd = self._build_modern_pandoc_cmd

        return build_pandoc_cmd(
            out_markup,
            strip_raw,
            out_filename,
            html_filename,
        )

    def convert(
        self,
        post: Post,
        out_markup: str,
        strip_raw: bool,
        wp_attach: bool,
        links: dict[str, str],
        out_filename: str,
    ):
        """
        Convert text from one markup language to another.
        """
        if not self.supports(post.markup):
            return

        with tempfile.NamedTemporaryFile(
            "w",
            suffix=".html",
            encoding="utf-8",
        ) as fp:
            html_filename = fp.name
            html_content = self._wrap_into_html(post)
            fp.write(html_content)
            fp.flush()  # avoid buffering, pandoc needs the file on disk

            cmd = self._build_pandoc_cmd(
                out_markup,
                strip_raw,
                out_filename,
                html_filename,
            )

            try:
                rc = subprocess.call(cmd)
                if rc < 0:
                    error = f"Child was terminated by signal {-rc}"
                    sys.exit(error)

                elif rc > 0:
                    error = "Please, check your Pandoc installation."
                    sys.exit(error)
            except OSError as e:
                error = f"Pandoc execution failed: {e}"
                sys.exit(error)

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
