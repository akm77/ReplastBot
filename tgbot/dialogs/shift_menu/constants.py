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


class ShiftDialogId(str, Enum):
    SHIFT_DIALOG_EXIT = "sdi_exit"
    SHIFT_LIST = "sdi00"
    SHIFT_SELECT = "sdi01"
    SHIFT_STAFF = "sdi02"
    SHIFT_STAFF_COLUMN = "sdi03"
    SHIFT_ACTIVITY = "sdi04"
    SHIFT_ACTIVITY_COLUMN = "sdi05"
    SHIFT_MATERIAL = "sdi06"
    SHIFT_MATERIAL_COLUMN = "sdi07"
    SHIFT_PRODUCT = "sdi08"
    SHIFT_PRODUCT_COLUMN = "sdi09"
    SELECT_SHIFT_STAFF = "sdi10"
    SWITCH_TO_SHIFT_LIST = "sdi11"
    DONT_SAVE_AND_SWITCH_TO_SHIFT_LIST = "sdi12"
    SAVE_AND_SWITCH_TO_SHIFT_LIST = "sdi13"
    STAFF_LIST = "sdi14"
    ENTER_WORKED_HOURS = "sdi15"
    SHIFT_DURATION_BUTTON = "sdi16"
    NEW_SHIFT = "sdi17"

    def __str__(self) -> str:
        return str.__str__(self)
