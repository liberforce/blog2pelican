from blog2pelican.adapters.blog_readers.dotclear import DotclearReader
from blog2pelican.domain.entities.posts import Post


def test_simple():
    reader = DotclearReader()
    posts = reader.read_posts("tests/data/dotclear/standalone/posts/simple.txt")
    actual = next(posts)
    expected = Post(
        title="En direct d'Istanbul",
        content="<p>first paragraph</p>",
        filename="en-direct-distanbul",
        date="2008-07-07 11:07",
        author="TEST-GANDI",
        categories=["Life"],
        tags=["GUADEC", "GNOME"],
        status="published",
        kind="article",
        markup="html",
    )

    assert actual == expected


def test_shortest_post():
    reader = DotclearReader()
    posts = reader.read_posts(
        "tests/data/dotclear/standalone/posts/favorite-command-after-a-clean-mandriva-install.txt"
    )
    actual = next(posts)
    expected = Post(
        title="Favorite command after a clean Mandriva Install...",
        content="<pre>\nurpme -a mono\n</pre>",
        filename="favorite-command-after-a-clean-mandriva-install",
        date="2008-03-26 00:48",
        author="LM2153-GANDI",
        categories=["Computers / Informatique"],
        tags=["mandriva"],
        status="published",
        kind="article",
        markup="html",
    )

    assert actual == expected


def test_embedded_image():
    reader = DotclearReader()
    posts = reader.read_posts(
        "tests/data/dotclear/standalone/posts/guadec-2007-the-offline-desktop.txt"
    )
    actual = next(posts)
    expected = Post(
        title="GUADEC 2007: The offline desktop",
        content='<p><img alt="" src="/public/guadec/2007/offline-desktop.png" /></p>',
        filename="guadec-2007-the-offline-desktop",
        date="2007-07-23 23:43",
        author="LM2153-GANDI",
        categories=["Computers / Informatique"],
        tags=["bande dessinée", "GUADEC"],
        status="published",
        kind="article",
        markup="html",
    )

    assert actual == expected


def test_long_line():
    reader = DotclearReader()
    posts = reader.read_posts(
        "tests/data/dotclear/standalone/posts/you-like-linux-tell-it-to-the-world.txt"
    )
    actual = next(posts)
    expected = Post(
        title="You like Linux ? Tell it to the world !",
        content='<p>Help gather some stats and reach the 1,000,000 people who like Linux and\nOpen Source Software. It takes 30 seconds to fill the form on <a href="http://1-million-tux.linux-befehle.org">The million Tux</a>.</p>',
        filename="you-like-linux-tell-it-to-the-world",
        date="2010-04-07 16:08",
        author="LM2153-GANDI",
        categories=["Computers / Informatique"],
        tags=["linux"],
        status="published",
        kind="article",
        markup="html",
    )

    assert actual == expected
