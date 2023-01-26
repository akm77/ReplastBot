from aiogram.dispatcher.filters.state import StatesGroup, State


class ShiftMenu(StatesGroup):
    select_shift = State()
    select_date = State()


