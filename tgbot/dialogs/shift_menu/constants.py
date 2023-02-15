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
    SHIFT_DURATION_BUTTON = "sdi02"
    ENTER_SHIFT_DURATION = "sdi03"
    SHIFT_NEW_SHIFT = "sdi04"
    SHIFT_NUMBER_SELECT = "sdi05"
    SHIFT_STAFF = "sdi06"
    SHIFT_STAFF_COLUMN = "sdi07"
    ENTER_WORKED_HOURS = "sdi08"
    SHIFT_ACTIVITY = "sdi09"
    SHIFT_ACTIVITY_COLUMN = "sdi10"
    ENTER_ACTIVITY_COMMENT = "sdi11"
    SHIFT_MATERIAL = "sdi12"
    SHIFT_MATERIAL_COLUMN = "sdi13"
    SHIFT_PRODUCT = "sdi14"
    SHIFT_PRODUCT_COLUMN = "sdi15"
    SWITCH_TO_SHIFT_LIST = "sdi16"
    DONT_SAVE_AND_SWITCH_TO_SHIFT_LIST = "sdi17"
    SAVE_AND_SWITCH_TO_SHIFT_LIST = "sdi18"
    SELECT_FROM_DCT = "sdi19"
    DCT_LIST = "sdi20"

    def __str__(self) -> str:
        return str.__str__(self)


class SelectDictionary(str, Enum):
    Employee = "dct01"
    Activity = "dct02"
    Product = "dct03"
    Material = "dct04"

    def __str__(self) -> str:
        return str.__str__(self)