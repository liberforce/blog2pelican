from dataclasses import dataclass
from typing import Literal

from .base import ImportSettings


@dataclass
class MediumImportSettings(ImportSettings):
    origin: Literal["medium"]
