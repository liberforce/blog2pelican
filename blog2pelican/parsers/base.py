from typing import Any
import abc


class BlogParser(abc.ABC):
    @abc.abstractmethod
    def parse(self, path: str) -> tuple[Any]:
        """
        path: path to the file or dir containing the blog data to parse.
        """
