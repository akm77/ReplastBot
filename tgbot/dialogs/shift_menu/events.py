from typing import Any

from aiogram_dialog import DialogManager
from aiogram_dialog.context.events import ChatEvent
from aiogram_dialog.widgets.kbd import ManagedScrollingGroupAdapter


async def on_start_shift_dialog(start_data: Any, manager: DialogManager):
    pass


async def on_shift_list_page_changed(c: ChatEvent, adapter: ManagedScrollingGroupAdapter, manager: DialogManager):
    pass
