import tempfile

from blog2pelican.app.use_cases.convert_post import ConvertPostUseCase
from blog2pelican.domain.entities.posts import Post
from blog2pelican.domain.entities.settings import DotclearSettings


def test_simple():
    post = Post(
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

    with tempfile.TemporaryDirectory() as output_dir:
        settings = DotclearSettings(
            input=None,
            engine="dotclear",
            output_dir=output_dir,
            markup="markdown",
            allowed_authors=None,
            dircat=False,
        )
        uc = ConvertPostUseCase()
        actual = uc.convert(post, settings, output_dir)

    expected = Post(
        title="En direct d'Istanbul",
        content="first paragraph\n",
        filename="en-direct-distanbul",
        date="2008-07-07 11:07",
        author="TEST-GANDI",
        categories=["Life"],
        tags=["GUADEC", "GNOME"],
        status="published",
        kind="article",
        markup="markdown",
    )
    assert actual == expected
