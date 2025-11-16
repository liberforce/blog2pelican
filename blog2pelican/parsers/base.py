import abc
from collections.abc import Generator

from blog2pelican.entities.import_settings import ImportSettings
from blog2pelican.entities.posts import PelicanPost


class BlogParser(abc.ABC):
    def __init__(self, settings: ImportSettings):
        self.settings = settings

    @abc.abstractmethod
    def parse(self, path: str) -> Generator[PelicanPost]:
        """
        path: path to the file or dir containing the blog data to parse.
        """
