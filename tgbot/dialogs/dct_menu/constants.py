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
    DCT_ITEM_EDIT_DIGITAL_VALUE = "dmi08"
    SWITCH_TO_SHOW_DCT = "dmi09"
    CONTENT_TYPE_FLOAT = "dmi10"
    CONTENT_TYPE_STR = "dmi11"
    IS_PROVIDER_STATE = "dmi12"
    IS_BUYER_STATE = "dmi13"

    def __str__(self) -> str:
        return str.__str__(self)
