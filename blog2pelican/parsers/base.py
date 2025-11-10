from typing import Any
import abc


class BlogParser(abc.ABC):
    @abc.abstractmethod
    def parse_from_file(self, filename: str) -> tuple[Any]: ...
