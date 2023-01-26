from datetime import date
from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, ManagedScrollingGroupAdapter

from . import states, constants


async def on_date_selected(c: CallbackQuery, widget: Any, manager: DialogManager, selected_date: date):
    w: ManagedScrollingGroupAdapter = manager.dialog().find(constants.ScrollingGroupId.SHIFT_GROUP)
    w.

    await manager.switch_to(states.ShiftMenu.select_shift)


async def on_shift_navigator(c: CallbackQuery, button: Button, manager: DialogManager):
    pass


async def on_select_shift(c: CallbackQuery, button: Button, manager: DialogManager, shift_id: str):
    pass


async def on_new_shift(c: CallbackQuery, widget: Any, manager: DialogManager, shift_date: date):
    pass


async def on_delete_shift(c: CallbackQuery, widget: Any, manager: DialogManager, shift_date: date, shift_number: int):
    pass
