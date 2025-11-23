from dataclasses import dataclass
from typing import Literal

from .base import Settings


@dataclass
class FeedSettings(Settings):
    engine: Literal["feed"]
