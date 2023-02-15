from aiogram.dispatcher.filters.state import StatesGroup, State


class ShiftMenu(StatesGroup):
    select_shift = State()
    select_shift_date = State()
    select_new_shift_date = State()
    select_new_shift_number = State()
    edit_shift = State()
    edit_shift_duration = State()
    enter_hours_worked = State()
    enter_activity_comment = State()
    multi_select_from_dct = State()
    select_from_dct = State()


