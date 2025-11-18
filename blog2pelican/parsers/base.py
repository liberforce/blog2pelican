import abc
from collections.abc import Generator
from typing import Generic, TypeVar

from blog2pelican.domain.entities.posts import PelicanPost
from blog2pelican.domain.entities.settings import Settings

S = TypeVar("S", bound=Settings)


class BlogParser(abc.ABC, Generic[S]):
    settings: S | None

    def __init__(self):
        self.settings = None

    def use_settings(self, settings: S):
        self.settings = settings

    @abc.abstractmethod
    def parse(self, path: str) -> Generator[PelicanPost]:
        """
        path: path to the file or dir containing the blog data to parse.
        """
