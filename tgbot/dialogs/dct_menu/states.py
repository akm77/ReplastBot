from aiogram.dispatcher.filters.state import StatesGroup, State


class DictMenuStates(StatesGroup):
    select_dct = State()
    show_dct = State()
    show_dct_item = State()
    edit_dct_item = State()
    select_dct_item = State()
