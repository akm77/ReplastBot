from enum import Enum


class ShiftNavigatorButton(str, Enum):
    STAFF = "snb00"
    PRODUCT = "snb01"
    MATERIAL = "snb02"
    BACK = "snb03"
    CALENDAR = "snb04"
    NEXT = "snb05"
    ADD_SHIFT = "snb06"
    DEL_SHIFT = "snb07"
    FIRST = "snb08"
    LAST = "snb09"

    def __str__(self) -> str:
        return str.__str__(self)


class ScrollingGroupId(str, Enum):
    SHIFT_SELECT = "sgi_ss"
    SHIFT_GROUP = "sgi_sg"

    def __str__(self) -> str:
        return str.__str__(self)
