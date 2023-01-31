from typing import Any

from ...widgets.aiogram_dialog import DialogManager
from ...widgets.aiogram_dialog.context.events import ChatEvent
from ...widgets.aiogram_dialog.widgets.kbd import ManagedScrollingGroupAdapter
from ...widgets.aiogram_dialog.widgets.managed import ManagedWidgetAdapter


async def on_start_shift_dialog(start_data: Any, manager: DialogManager):
    pass


async def on_shift_list_page_changed(c: ChatEvent, adapter: ManagedScrollingGroupAdapter, manager: DialogManager):
    pass


async def on_employee_state_changed(event: ChatEvent,
                                    adapter: ManagedWidgetAdapter,
                                    manager: DialogManager,
                                    item_id: str):
    pass
