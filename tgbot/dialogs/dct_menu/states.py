from aiogram.dispatcher.filters.state import StatesGroup, State


class DictMenuStates(StatesGroup):
    select_dct = State()
