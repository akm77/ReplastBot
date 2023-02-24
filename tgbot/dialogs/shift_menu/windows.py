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
        keyboards.shift_staff_kbd(onclick.on_select_shift_object),
        keyboards.shift_activity_kbd(onclick.on_select_shift_object),
        keyboards.shift_product_kbd(onclick.on_select_shift_object),
        keyboards.shift_material_kbd(onclick.on_select_shift_object),
        Row(Cancel(Const("<<"),
                   id=constants.ShiftDialogId.SHIFT_DIALOG_EXIT,
                   on_click=onclick.on_click_exit,
                   result=True),
            Button(Const("💬"),
                   id=constants.ShiftDialogId.SEND_TO_JOURNAL,
                   on_click=onclick.on_send_to_journal)
            ),
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
                 id=constants.ShiftDialogId.SHIFT_NEW_SHIFT,
                 state=ShiftMenu.select_new_shift_date),
        state=ShiftMenu.edit_shift,
        getter=getters.get_selected_shift
    )


def set_shift_duration_window():
    return Window(
        Format("Смена 👇\nДата: {shift_date} номер: {shift_number} время: {shift_duration} ч"),
        TextInput(id=constants.ShiftDialogId.ENTER_SHIFT_DURATION,
                  type_factory=float,
                  on_success=events.on_success_enter_shift_duration,
                  on_error=events.on_error_enter_shift_duration),
        state=ShiftMenu.edit_shift_duration,
        getter=getters.get_selected_shift
    )


def new_shift_date_window(tz: str = "UTC", calendar_locale=(None, None)):
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


def new_shift_number_window(tz: str = "UTC", calendar_locale=(None, None)):
    return Window(
        Format("Текущая смена☞ дата: {shift_date} номер: {shift_number} время: {shift_duration} ч\n"
               "Дата новой смены: {new_shift_date}\n"
               "Выбрать номер смены👇"),
        keyboards.select_shift_number_kbd(),
        keyboards.switch_to_shift_list_kbd(onclick.on_cancel_button_click, onclick.on_save_button_click),
        state=ShiftMenu.select_new_shift_number,
        getter=getters.get_new_shift
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


def multi_select_from_dct_window():
    return Window(
        Const("Выберите из списка"),
        keyboards.multi_select_from_dct_kbd(on_click=onclick.on_multi_select_dct_item),
        keyboards.switch_to_shift_list_kbd(onclick.on_cancel_button_click, onclick.on_save_button_click),
        SwitchTo(Const("<<"),
                 id="ms_d_bsm",
                 state=ShiftMenu.select_shift),
        state=ShiftMenu.multi_select_from_dct,
        getter=getters.multi_select_from_dct
    )


def select_from_dct_window():
    return Window(
        Const("Выберите из списка"),
        keyboards.select_from_dct_kbd(on_click=onclick.on_select_dct_item),
        SwitchTo(Const("<<"),
                 id="s_d_bsm",
                 state=ShiftMenu.select_shift),
        state=ShiftMenu.select_from_dct,
        getter=getters.select_from_dct
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


def set_activity_comment():
    return Window(
        Format("Текущая смена☞ дата: {shift_date} номер: {shift_number} время: {shift_duration} ч\n"
               "Работа - {activity_name}.\n"
               "Комментарий: {activity_comment}.\n"
               "👇Введите комментарий. Убрать комментарий ☞ *-👇"),
        TextInput(id=constants.ShiftDialogId.ENTER_ACTIVITY_COMMENT,
                  type_factory=str,
                  on_success=events.on_success_enter_activity_comment,
                  on_error=events.on_error_enter_activity_comment),
        state=ShiftMenu.enter_activity_comment,
        getter=getters.get_shift_activity
    )


def set_material_quantity():
    return Window(
        Format("Текущая смена☞ дата: {shift_date} номер: {shift_number} время: {shift_duration} ч\n"
               "Сырье - {material_name}.\n"
               "👇Количество: {material_quantity}.👇"),
        TextInput(id=constants.ShiftDialogId.ENTER_MATERIAL_QUANTITY,
                  type_factory=str,
                  on_success=events.on_success_enter_material_quantity,
                  on_error=events.on_error_enter_material_quantity),
        state=ShiftMenu.enter_material_quantity,
        getter=getters.get_shift_material_quantity
    )


def set_product_bag_quantity():
    return Window(
        Format("Текущая смена☞ дата: {shift_date} номер: {shift_number} время: {shift_duration} ч\n"
               "Продукция - {product_name}.\n"
               "👇Мешок: {bag_number} Количество: {product_quantity}.👇"),
        TextInput(id=constants.ShiftDialogId.ENTER_PRODUCT_BAG_QUANTITY,
                  type_factory=str,
                  on_success=events.on_success_enter_product_bag_quantity,
                  on_error=events.on_error_enter_product_bag_quantity),
        state=ShiftMenu.enter_product_bag_quantity,
        getter=getters.get_shift_product_bag_quantity
    )
