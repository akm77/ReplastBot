from . import keyboards, getters, onclick, events, constants
from ...dialogs.shift_menu.states import ShiftMenu
from ...widgets.aiogram_dialog import Window
from ...widgets.aiogram_dialog.widgets.input import TextInput
from ...widgets.aiogram_dialog.widgets.kbd import Row, Button, Calendar, Back, SwitchTo, Cancel
from ...widgets.aiogram_dialog.widgets.text import Const, Format


def shift_window():
    return Window(
        Const("Смены по датам"),
        keyboards.shift_list_kbd(onclick.on_select_shift, events.on_shift_list_page_changed, onclick.on_enter_page),
        keyboards.shift_staff_kbd(onclick.on_select_staff_member),
        keyboards.shift_activity_kbd(onclick.on_select_activity),
        keyboards.shift_product_kbd(onclick.on_select_product),
        keyboards.shift_material_kbd(onclick.on_select_material),
        Cancel(Const("<<"),
               id=constants.ShiftDialogId.SHIFT_DIALOG_EXIT,
               on_click=onclick.on_click_exit,
               result=True),
        state=ShiftMenu.select_shift,
        getter=getters.get_shift_list
    )


def edit_shift_window():
    return Window(
        Format("Смена 👇\nДата: {shift_date} номер: {shift_number} время: {shift_duration} ч"),
        Button(Format("<< {shift_duration} ч >>"),
               id=constants.ShiftDialogId.SHIFT_DURATION_BUTTON,
               on_click=onclick.on_select_shift_duration),
        SwitchTo(Const("<< + >>"),
                 id=constants.ShiftDialogId.NEW_SHIFT,
                 state=ShiftMenu.select_new_shift_date),
        state=ShiftMenu.edit_shift,
        getter=getters.get_selected_shift
    )


def edit_shift_duration_window():
    return Window(
        Format("Смена 👇\nДата: {shift_date} номер: {shift_number} время: {shift_duration} ч"),
        TextInput(id=constants.ShiftDialogId.ENTER_SHIFT_DURATION,
                  type_factory=float,
                  on_success=events.on_success_enter_shift_duration),
        state=ShiftMenu.edit_shift_duration,
        getter=getters.get_selected_shift
    )


def new_shift_window(tz: str = "UTC", calendar_locale=(None, None)):
    return Window(
        Format("Текущая смена☞ дата: {shift_date} номер: {shift_number} время: {shift_duration} ч\n"
               "Выберите дату новой смены👇"),
        Calendar(id='calendar',
                 on_click=onclick.on_date_selected,
                 marked_day=events.mark_shift_day,
                 tz=tz, calendar_locale=calendar_locale),
        state=ShiftMenu.select_new_shift_date,
        getter=getters.get_selected_shift
    )


def select_shift_date_window(tz: str = "UTC", calendar_locale=(None, None)):
    return Window(
        Const("Выберите дату"),
        Calendar(id='calendar',
                 marked_day=events.mark_shift_day,
                 on_click=onclick.on_date_selected,
                 tz=tz,
                 calendar_locale=calendar_locale),
        Back(Const("<<"),
             on_click=onclick.on_click_calendar_back),
        state=ShiftMenu.select_shift_date
    )


def select_staff_window():
    return Window(
        Const("Выберите сотрудников"),
        keyboards.select_staff_kbd(onclick.on_select_employee, events.on_employee_state_changed, None, None),
        keyboards.switch_to_shift_list_kbd(onclick.on_cancel_button_click, onclick.on_save_button_click),
        state=ShiftMenu.select_staff,
        getter=getters.get_employee_list
    )


def update_staff_member_window():
    return Window(
        Format("Отработанное время {employee_shift_date} смена {employee_shift_number} для {employee_name}.\n"
               "Старое значение - {employee_hours_worked} ч.\n"
               "👇Введите новое значение.👇"),
        TextInput(id=constants.ShiftDialogId.ENTER_WORKED_HOURS,
                  type_factory=float,
                  on_success=events.on_success_enter_hours_worked,
                  on_error=events.on_error_enter_hours_worked),
        state=ShiftMenu.enter_hours_worked,
        getter=getters.get_staff_employee
    )
