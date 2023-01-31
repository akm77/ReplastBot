import operator

from . import onclick, events, constants
from .constants import ShiftDialogId
from .states import ShiftMenu
from ...widgets.aiogram_dialog.widgets.kbd import ScrollingGroup, Select, Column, Multiselect, SwitchTo, Row
from ...widgets.aiogram_dialog.widgets.text import Format, Const


def shift_list_kbd(on_click, on_page_changed, on_enter_page):
    return ScrollingGroup(
        Select(
            Format("{item[0]}"),
            id=ShiftDialogId.SHIFT_SELECT,
            item_id_getter=operator.itemgetter(1),
            items="shift_list",
            on_click=on_click
        ),
        id=ShiftDialogId.SHIFT_LIST,
        width=1, height=1,
        on_page_changed=on_page_changed,
        on_enter_page=on_enter_page
    )


def shift_staff_kbd(on_click):
    return Column(
        Select(
            Format("{item[0]}"),
            id=ShiftDialogId.SHIFT_STAFF,
            item_id_getter=operator.itemgetter(1),
            items="shift_staff",
            on_click=on_click),
        id=ShiftDialogId.SHIFT_STAFF_COLUMN)


def shift_activity_kbd(on_click):
    return Column(
        Select(
            Format("{item[0]}"),
            id=ShiftDialogId.SHIFT_ACTIVITY,
            item_id_getter=operator.itemgetter(1),
            items="shift_activity",
            on_click=on_click
        ),
        id=ShiftDialogId.SHIFT_ACTIVITY_COLUMN)


def shift_material_kbd(on_click):
    return Column(
        Select(
            Format("{item[0]}"),
            id=ShiftDialogId.SHIFT_MATERIAL,
            item_id_getter=operator.itemgetter(1),
            items="shift_material",
            on_click=on_click
        ),
        id=ShiftDialogId.SHIFT_MATERIAL_COLUMN)


def shift_product_kbd(on_click):
    return Column(
        Select(
            Format("{item[0]}"),
            id=ShiftDialogId.SHIFT_PRODUCT,
            item_id_getter=operator.itemgetter(1),
            items="shift_product",
            on_click=on_click
        ),
        id=ShiftDialogId.SHIFT_PRODUCT_COLUMN)


def select_staff_kbd(on_click, on_state_changed, on_page_changed, on_enter_page):
    return ScrollingGroup(
        Multiselect(
            Format("✓ {item[0]}"),
            Format("{item[0]}"),
            id=ShiftDialogId.SELECT_SHIFT_STAFF,
            item_id_getter=operator.itemgetter(1),
            items="employee",
            on_click=on_click,
            on_state_changed=on_state_changed
        ),
        id=ShiftDialogId.STAFF_LIST,
        width=1, height=10,
        hide_on_single_page=True,
        on_page_changed=on_page_changed,
        on_enter_page=on_enter_page
    )


def switch_to_shift_list_kbd(on_click):
    return Row(SwitchTo(Const("<< ✘"),
                        id=constants.ShiftDialogId.DONT_SAVE_AND_SWITCH_TO_SHIFT_LIST,
                        state=ShiftMenu.select_shift,
                        on_click=None),
               SwitchTo(Const("<< ✔︎"),
                        id=constants.ShiftDialogId.SAVE_AND_SWITCH_TO_SHIFT_LIST,
                        state=ShiftMenu.select_shift,
                        on_click=on_click),
               id=constants.ShiftDialogId.SWITCH_TO_SHIFT_LIST
               )