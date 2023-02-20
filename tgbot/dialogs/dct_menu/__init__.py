from . import windows, events
from ...widgets.aiogram_dialog import Dialog


def dct_menu_dialogs(tz: str = "UTC", calendar_locale=(None, None)):
    return [
        Dialog(
            windows.dct_menu_window()
        )
    ]