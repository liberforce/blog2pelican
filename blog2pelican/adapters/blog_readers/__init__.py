from blog2pelican.domain.ports.blog_reader import BlogReader


def create_blog_reader(engine: str) -> BlogReader:
    if engine == "blogger":
        from blog2pelican.adapters.blog_readers.blogger import BloggerReader

        return BloggerReader()
    elif engine == "dotclear":
        from blog2pelican.adapters.blog_readers.dotclear import DotclearReader

        return DotclearReader()
    elif engine == "medium":
        from blog2pelican.adapters.blog_readers.medium import MediumReader

        return MediumReader()
    elif engine == "tumblr":
        from blog2pelican.adapters.blog_readers.tumblr import TumblrReader

        return TumblrReader()
    elif engine == "wordpress":
        from blog2pelican.adapters.blog_readers.wordpress import WordPressReader

        return WordPressReader()
    elif engine == "feed":
        from blog2pelican.adapters.blog_readers.feed import FeedReader

        return FeedReader()
    else:
        raise ValueError(f"Unhandled blog engine: {engine}")
