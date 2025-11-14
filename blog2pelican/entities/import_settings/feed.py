from dataclasses import dataclass
from typing import Literal

from .base import ImportSettings


@dataclass
class FeedImportSettings(ImportSettings):
    origin: Literal["feed"]
