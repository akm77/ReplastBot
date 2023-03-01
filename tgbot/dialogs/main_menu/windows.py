from . import states, onclick, constants
from ...widgets.aiogram_dialog import Window
from ...widgets.aiogram_dialog.widgets.kbd import Button, Cancel, Row
from ...widgets.aiogram_dialog.widgets.text import Const


def main_menu_window():
    return Window(
        Const("Выберите действие"),
        Row(Button(Const("Справочники"),
                   id=constants.MainMenuIds.SHOW_DCT,
                   on_click=onclick.on_click_dct_button),
            Button(Const("Производство"),
                   id=constants.MainMenuIds.SHOW_PRODUCTION,
                   on_click=onclick.on_click_shift_button)),
        Button(Const("Экспорт ⇧"),
               id=constants.MainMenuIds.EXPORT_PRODUCTION,
               on_click=onclick.on_click_export_production
               ),
        Cancel(Const("<<")),
        state=states.MainMenu.select_action
    )
