from aiogram import Dispatcher


from . import shift_menu
from ..widgets.aiogram_dialog import DialogRegistry


def setup_dialogs(dp: Dispatcher, tz: str = "UTC", calendar_locale=(None, None)):
    registry = DialogRegistry(dp)
    for dialog in [
        *shift_menu.shift_menu_dialogs(tz, calendar_locale),
    ]:
        registry.register(dialog)  # register a dialog
