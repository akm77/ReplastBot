import operator

from . import constants, onclick
from ...widgets.aiogram_dialog.widgets.kbd import ScrollingGroup, Button, Cancel, Select
from ...widgets.aiogram_dialog.widgets.text import Const, Format
from ...models.erp_dict import DICT_LIST


def get_dct_buttons(on_click):
    return [Button(Const(dct.hr_names["table_name"]),
                   id=dct.__name__,
                   on_click=on_click) for dct in DICT_LIST]


def dct_list_kbd(on_click, on_page_changed=None, on_enter_page=None):
    return ScrollingGroup(
        *get_dct_buttons(on_click),
        id=constants.DctMenuIds.DCT_SCROLLING_GROUP,
        width=2, height=10,
        on_page_changed=on_page_changed,
        on_enter_page=on_enter_page,
        hide_on_single_page=True
    )


def simple_dct_items_kbd(on_click, on_page_changed=None, on_enter_page=None):
    return ScrollingGroup(
        Select(
            Format("{item[0]}"),
            id=constants.DctMenuIds.DCT_ITEMS,
            item_id_getter=operator.itemgetter(1),
            items="items",
            on_click=on_click,
        ),
        id=constants.DctMenuIds.DCT_ITEMS_SCROLLING_GROUP,
        width=1, height=10,
        on_page_changed=on_page_changed,
        on_enter_page=on_enter_page,
        hide_on_single_page=True
    )
