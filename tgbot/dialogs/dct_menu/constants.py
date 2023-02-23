from enum import Enum


class DctMenuIds(str, Enum):
    DCT_SCROLLING_GROUP = "dmi00"
    DCT_ITEMS_SCROLLING_GROUP = "dmi01"
    DCT_ITEMS = "dmi02"
    DCT_ITEM_STATE = "dmi03"
    DCT_ITEM_EDIT_BUTTON = "dmi04"
    DCT_ITEM_DELETE_BUTTON = "dmi05"
    DCT_ITEM_CONTENT = "dmi06"
    ADD_DCT_ITEM = "dmi07"

    def __str__(self) -> str:
        return str.__str__(self)


class DctEditMode(str, Enum):
    NEW_RECORD = "dem00"
    UPDATE_RECORD = "dem02"
    DELETE_RECORD = "dmi03"

    def __str__(self) -> str:
        return str.__str__(self)
