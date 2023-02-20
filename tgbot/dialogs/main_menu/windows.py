from . import states, onclick
from ...widgets.aiogram_dialog import Window
from ...widgets.aiogram_dialog.widgets.kbd import Button, Cancel, Row
from ...widgets.aiogram_dialog.widgets.text import Const


def main_menu_window():
    return Window(
        Const("Выберите действие"),
        Row(Button(Const("Справочники"), id="1st", on_click=onclick.on_click_dct_button),
            Button(Const("Производство"), id="2nd", on_click=onclick.on_click_shift_button)),
        Cancel(Const("<<")),
        state=states.MainMenu.select_action
    )
