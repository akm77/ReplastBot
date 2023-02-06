from . import windows
from ...widgets.aiogram_dialog import Dialog


def main_menu_dialogs(tz: str = "UTC", calendar_locale=(None, None)):
    return [
        Dialog(
            windows.main_menu_window(),
            on_start=None,
            on_process_result=None
        )
    ]
