from aiogram.types import CallbackQuery

from ..dct_menu.states import DictMenuStates
from ..shift_menu.states import ShiftMenu
from ...widgets.aiogram_dialog import DialogManager
from ...widgets.aiogram_dialog.widgets.kbd import Button


async def on_click_dct_button(c: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(DictMenuStates.select_dct)


async def on_click_shift_button(c: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(ShiftMenu.select_shift)
