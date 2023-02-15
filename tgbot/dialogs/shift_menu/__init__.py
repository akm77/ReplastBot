from . import windows, events
from ...widgets.aiogram_dialog import Dialog


def shift_menu_dialogs(tz: str = "UTC", calendar_locale=(None, None)):
    return [
        Dialog(
            windows.shift_window(),
            windows.select_shift_date_window(tz, calendar_locale),
            windows.update_staff_member_window(),
            windows.edit_shift_window(),
            windows.new_shift_date_window(tz, calendar_locale),
            windows.new_shift_number_window(),
            windows.edit_shift_duration_window(),
            windows.multi_select_from_dct_window(),
            windows.update_activity_comment(),
            on_start=events.on_start_shift_dialog,
            on_process_result=events.on_process_result_shift_dialog,
            on_close=events.on_close_shift_dialog
        )
    ]
