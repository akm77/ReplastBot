from enum import Enum


class DctMenuIds(str, Enum):
    DCT_SCROLLING_GROUP = "dmi00"

    def __str__(self) -> str:
        return str.__str__(self)
