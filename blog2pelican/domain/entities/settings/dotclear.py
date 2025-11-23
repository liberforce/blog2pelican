from dataclasses import dataclass
from typing import Literal

from .base import Settings


@dataclass
class DotclearSettings(Settings):
    engine: Literal["dotclear"]
