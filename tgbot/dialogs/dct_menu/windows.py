from . import keyboards, states, onclick
from ...widgets.aiogram_dialog import Window
from ...widgets.aiogram_dialog.widgets.kbd import Cancel
from ...widgets.aiogram_dialog.widgets.text import Const


def dct_menu_window():
    return Window(
        Const("Справочники"),
        keyboards.dct_list_kbd(on_click=onclick.on_click_dct),
        Cancel(Const("<<")),
        state=states.DictMenuStates.select_dct
    )
