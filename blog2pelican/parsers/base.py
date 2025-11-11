import abc
from collections.abc import Generator

from blog2pelican.entities.posts import PelicanPost


class BlogParser(abc.ABC):
    @abc.abstractmethod
    def parse(self, path: str) -> Generator[PelicanPost]:
        """
        path: path to the file or dir containing the blog data to parse.
        """
