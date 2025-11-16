from blog2pelican.entities.import_settings import DotclearImportSettings
from blog2pelican.entities.posts import PelicanPost
from blog2pelican.parsers.dotclear import DotclearParser


def test_simple():
    settings = DotclearImportSettings(
        "dotclear",
        input=None,
        output=None,
        markup=None,
        author=None,
        dircat=None,
    )
    parser = DotclearParser()
    posts = parser.parse("tests/data/dotclear/standalone/posts/simple.txt")
    actual = next(posts)
    expected = PelicanPost(
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
    settings = DotclearImportSettings(
        "dotclear",
        input=None,
        output=None,
        markup=None,
        author=None,
        dircat=None,
    )
    parser = DotclearParser()
    posts = parser.parse(
        "tests/data/dotclear/standalone/posts/favorite-command-after-a-clean-mandriva-install.txt"
    )
    actual = next(posts)
    expected = PelicanPost(
        title="Favorite command after a clean Mandriva Install...",
        content="<pre>urpme -a mono</pre>",
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
    settings = DotclearImportSettings(
        "dotclear",
        input=None,
        output=None,
        markup=None,
        author=None,
        dircat=None,
    )
    parser = DotclearParser()
    posts = parser.parse(
        "tests/data/dotclear/standalone/posts/guadec-2007-the-offline-desktop.txt"
    )
    actual = next(posts)
    expected = PelicanPost(
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
