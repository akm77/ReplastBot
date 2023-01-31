from . import windows, events
from ...widgets.aiogram_dialog import Dialog


def shift_menu_dialogs(tz: str = "UTC", calendar_locale=(None, None)):
    return [
        Dialog(
            windows.shift_window(),
            windows.select_shift_date_window(tz, calendar_locale),
            windows.select_staff_window(),
            on_start=events.on_start_shift_dialog,
            on_process_result=None
        )
    ]
