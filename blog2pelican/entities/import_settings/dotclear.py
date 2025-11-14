from dataclasses import dataclass
from typing import Literal

from .base import ImportSettings


@dataclass
class DotclearImportSettings(ImportSettings):
    origin: Literal["dotclear"]
