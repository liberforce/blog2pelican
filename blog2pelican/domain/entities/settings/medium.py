from dataclasses import dataclass
from typing import Literal

from .base import Settings


@dataclass
class MediumSettings(Settings):
    origin: Literal["medium"]
