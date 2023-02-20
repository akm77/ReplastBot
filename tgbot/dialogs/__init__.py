from aiogram import Dispatcher


from . import shift_menu, main_menu, dct_menu
from ..widgets.aiogram_dialog import DialogRegistry


def setup_dialogs(dp: Dispatcher, tz: str = "UTC", calendar_locale=(None, None)):
    registry = DialogRegistry(dp)
    for dialog in [
        *shift_menu.shift_menu_dialogs(tz, calendar_locale),
        *main_menu.main_menu_dialogs(),
        *dct_menu.dct_menu_dialogs()
    ]:
        registry.register(dialog)  # register a dialog
