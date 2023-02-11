from aiogram.dispatcher.filters.state import StatesGroup, State


class ShiftMenu(StatesGroup):
    select_shift = State()
    select_new_shift_date = State()
    edit_shift = State()
    edit_shift_duration = State()
    select_shift_date = State()
    select_staff = State()
    enter_hours_worked = State()


