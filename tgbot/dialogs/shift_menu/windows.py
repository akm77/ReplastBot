from aiogram_dialog import Window
from aiogram_dialog.widgets.kbd import Calendar, Back, Cancel, Row, Button, Next
from aiogram_dialog.widgets.text import Const

from tgbot.dialogs.shift_menu.states import ShiftMenu
from . import keyboards, getters, onclick, constants


def shift_window():
    return Window(
        Const("Shift list"),
        keyboards.shift_list(onclick.on_select_shift),
        Row(Button(Const("<<"), id=constants.ShiftNavigatorButton.FIRST),
            Next(Const("#")),
            Button(Const(">>"), id=constants.ShiftNavigatorButton.FIRST)),
        Cancel(),
        state=ShiftMenu.select_shift,
        getter=getters.get_shift_list
    )
    # return Window(
    #     Const(("01.01.2023, смена: 1 (10 ч)\n"
    #            "---------------------\n"
    #            "Персонал\n"
    #            "Алена 10 ч.\n"
    #            "Иван 10 ч.\n"
    #            "---------------------\n"
    #            "Сырье\n"
    #            "Полигон 500- кг\n"
    #            "Крышка 600- кг\n"
    #            "---------------------\n"
    #            "Продукция\n"
    #            "ПГ #1086 500 кг\n"
    #            "ПГ #1087 600 кг\n"
    #            "ПЭТФ #1087 600 кг\n"
    #            )),
    #     keyboards.shift_navigator(onclick),
    #     # Calendar(id='calendar', on_click=selected.on_date_selected, when=is_date_select),
    #     state=ShiftMenu.select_shift,
    #     getter=getters.get_shift
    # )


def choose_shift_date_window():
    return Window(
        Const("Выберите дату"),
        Calendar(id='calendar', on_click=onclick.on_date_selected),
        Back(Const("<<")),
        state=ShiftMenu.select_date
    )
