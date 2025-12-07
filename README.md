# blog2pelican

This program is derived from `pelican-import` from the pelican official
repository. It aims at simplifying the migration for my own old dotclear blog.

If it's useful to someone else, that's great. I've however tested it only with
dotclear input, while trying to refactor the code for other blog engines and not
breaking anything.

## Markdown generation

### The state of markdown

Pandoc handles lots of different [markdown dialects](https://pandoc.org/MANUAL.html#pandocs-markdown).
To see the extensions supported by a dialect, like `markdown`:

```bash
pandoc --list-extensions=markdown
```

### Markdown dialect generated

While the original `pelican-import` uses the GitHub Flavored Markdown (`gfm`) as
its markdown dialect of choice, I'm trying to use
[Pandoc's markdown](https://pandoc.org/MANUAL.html#pandocs-markdown) instead
which opens for more flexibility in terms of supported output (exporting a
specific article to PDF or epub for example).

