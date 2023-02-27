from . import windows, events, states
from ...widgets.aiogram_dialog import Dialog


def dct_menu_dialogs(tz: str = "UTC", calendar_locale=(None, None)):
    return [
        Dialog(
            windows.dct_menu_window(),
            windows.show_dct_window(state=states.DictMenuStates.show_dct),
            windows.show_dct_window(state=states.DictMenuStates.select_dct_item),
            windows.show_dct_item_window(),
            windows.set_dct_item_window()
        )
    ]
