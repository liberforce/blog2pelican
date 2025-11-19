from blog2pelican.domain.ports.blog_reader import BlogReader


def create_blog_reader(origin: str) -> BlogReader:
    if origin == "blogger":
        from blog2pelican.adapters.blog_readers.blogger import BloggerReader

        return BloggerReader()
    elif origin == "dotclear":
        from blog2pelican.adapters.blog_readers.dotclear import DotclearReader

        return DotclearReader()
    elif origin == "medium":
        from blog2pelican.adapters.blog_readers.medium import MediumReader

        return MediumReader()
    elif origin == "tumblr":
        from blog2pelican.adapters.blog_readers.tumblr import TumblrReader

        return TumblrReader()
    elif origin == "wordpress":
        from blog2pelican.adapters.blog_readers.wordpress import WordPressReader

        return WordPressReader()
    elif origin == "feed":
        from blog2pelican.adapters.blog_readers.feed import FeedReader

        return FeedReader()
    else:
        raise ValueError(f"Unhandled origin {origin}")
