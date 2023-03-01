from enum import Enum


class MainMenuIds(str, Enum):
    SHOW_DCT = "mmi00"
    SHOW_PRODUCTION = "mmi01"
    EXPORT_PRODUCTION = "mmi02"

    def __str__(self) -> str:
        return str.__str__(self)
