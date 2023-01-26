from aiogram import Dispatcher
from aiogram_dialog import DialogRegistry

from . import shift_menu


def setup_dialogs(dp: Dispatcher):
    registry = DialogRegistry(dp)
    for dialog in [
        *shift_menu.shift_menu_dialogs(),
    ]:
        registry.register(dialog)  # register a dialog
