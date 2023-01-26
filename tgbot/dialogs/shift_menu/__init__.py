from aiogram_dialog import Dialog

from . import windows, events


def shift_menu_dialogs():
    return [
        Dialog(
            windows.shift_window(),
            windows.choose_shift_date_window(),
            on_start=events.on_start_shift_dialog,
            on_process_result=None
        )
    ]
