from blog2pelican.parsers.dotclear import DotclearParser
from blog2pelican.entities.posts import PelicanPost


def test_simple():
    parser = DotclearParser()
    posts = parser.parse("tests/data/dotclear/standalone/posts/simple.txt")
    actual = PelicanPost(*next(posts))
    expected = PelicanPost(
        title="En direct d'Istanbul",
        content="<p>first paragraph</p>",
        filename="en-direct-distanbul",
        date="2008-07-07 08:08",
        author="TEST-GANDI",
        categories=["Life"],
        tags=["GUADEC", "GNOME"],
        status="published",
        kind="article",
        in_markup="html",
    )

    assert actual == expected
