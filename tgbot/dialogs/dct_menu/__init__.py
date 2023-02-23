from . import windows, events
from ...widgets.aiogram_dialog import Dialog


def dct_menu_dialogs(tz: str = "UTC", calendar_locale=(None, None)):
    return [
        Dialog(
            windows.dct_menu_window(),
            windows.show_simple_dct_window(),
            windows.show_dct_item_window(),
            windows.set_dct_item_window()
        )
    ]
