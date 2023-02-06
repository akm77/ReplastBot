from . import states, onclick
from ...widgets.aiogram_dialog import Window
from ...widgets.aiogram_dialog.widgets.kbd import Button, Cancel, Row
from ...widgets.aiogram_dialog.widgets.text import Const


def main_menu_window():
    return Window(
        Const("Выберите действие"),
        Row(Button(Const("Новая смена"), id="1st"),
            Button(Const("Смены"), id="2nd")),
        Button(Const("<<"), id="_b", on_click=onclick.dialog_done),
        state=states.MainMenu.select_action
    )
