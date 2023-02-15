import operator

from . import onclick, events, constants
from .constants import ShiftDialogId
from .states import ShiftMenu
from ...widgets.aiogram_dialog.widgets.kbd import ScrollingGroup, Select, Column, Multiselect, SwitchTo, Row, Radio, \
    Button
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


def multi_select_from_dct_kbd(on_click=None, on_state_changed=None, on_page_changed=None, on_enter_page=None):
    return ScrollingGroup(
        Multiselect(
            Format("✓ {item[0]}"),
            Format("{item[0]}"),
            id=ShiftDialogId.MULTI_SELECT_FROM_DCT,
            item_id_getter=operator.itemgetter(1),
            items="items",
            on_click=on_click,
            on_state_changed=on_state_changed
        ),
        id=ShiftDialogId.MULTI_SELECT_DCT_LIST,
        width=1, height=10,
        hide_on_single_page=True,
        on_page_changed=on_page_changed,
        on_enter_page=on_enter_page
    )


def select_from_dct_kbd(on_click=None, on_page_changed=None, on_enter_page=None):
    return ScrollingGroup(
        Select(
            Format("{item[0]}"),
            id=ShiftDialogId.SELECT_FROM_DCT,
            item_id_getter=operator.itemgetter(1),
            items="items",
            on_click=on_click
        ),
        id=ShiftDialogId.DCT_LIST,
        width=1, height=10,
        hide_on_single_page=True,
        on_page_changed=on_page_changed,
        on_enter_page=on_enter_page
    )


def switch_to_shift_list_kbd(on_cancel_button_click, on_save_button_click):
    return Row(SwitchTo(Const("<< ✘"),
                        id=constants.ShiftDialogId.DONT_SAVE_AND_SWITCH_TO_SHIFT_LIST,
                        state=ShiftMenu.select_shift,
                        on_click=on_cancel_button_click),
               SwitchTo(Const("<< ✓"),
                        id=constants.ShiftDialogId.SAVE_AND_SWITCH_TO_SHIFT_LIST,
                        state=ShiftMenu.select_shift,
                        on_click=on_save_button_click),
               id=constants.ShiftDialogId.SWITCH_TO_SHIFT_LIST
               )


def select_shift_number_kbd(on_click=None, on_state_changed=None):
    return Row(Radio(
        Format("✓ ︎{item[0]}"),
        Format("︎{item[0]}"),
        id=constants.ShiftDialogId.SHIFT_NUMBER_SELECT,
        item_id_getter=operator.itemgetter(1),
        items="shift_numbers",
        on_click=on_click,
        on_state_changed=on_state_changed),
    )
