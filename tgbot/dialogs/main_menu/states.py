from aiogram.dispatcher.filters.state import StatesGroup, State


class MainMenu(StatesGroup):
    select_action = State()
