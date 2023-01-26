import operator

from aiogram_dialog.widgets.kbd import Row, Button, Group, Cancel, Column, Next, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format

from . import constants, onclick, events
from .constants import ScrollingGroupId


def shift_navigator(on_click):
    return Group(
        Row(
            Button(Const("Staff"), id=constants.ShiftNavigatorButton.STAFF),
            Button(Const("Product"), id=constants.ShiftNavigatorButton.PRODUCT),
            Button(Const("Material"), id=constants.ShiftNavigatorButton.MATERIAL)
        ),
        Row(
            Button(Const("<"), id=constants.ShiftNavigatorButton.BACK, on_click=onclick.on_shift_navigator),
            Next(Const("#")),
            Button(Const(">"), id=constants.ShiftNavigatorButton.NEXT, on_click=onclick.on_shift_navigator)
        ),
        Row(
            Button(Const("Add +"), id=constants.ShiftNavigatorButton.ADD_SHIFT, on_click=onclick.on_new_shift),
            Cancel(Const('Exit')),
            Button(Const("Del -"), id=constants.ShiftNavigatorButton.DEL_SHIFT, on_click=onclick.on_delete_shift)
        )
    )


def shift_list(on_click):
    return ScrollingGroup(
        Select(
            Format("{item[0]}"),
            id=ScrollingGroupId.SHIFT_SELECT,
            item_id_getter=operator.itemgetter(1),
            items="shift_list",
            on_click=on_click
        ),
        id=ScrollingGroupId.SHIFT_GROUP,
        width=1, height=1,
        on_page_changed=events.on_shift_list_page_changed
    )


def shift_staff():
    return Column(

    )
