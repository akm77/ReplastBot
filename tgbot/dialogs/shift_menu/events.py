import datetime
from typing import Any, Optional

from .states import ShiftMenu
from ...models.erp_shift import upsert_shift_staff, shift_update
from ...widgets.aiogram_dialog import DialogManager
from ...widgets.aiogram_dialog.context.events import ChatEvent, Data
from ...widgets.aiogram_dialog.widgets.input import TextInput
from ...widgets.aiogram_dialog.widgets.kbd import ManagedScrollingGroupAdapter
from ...widgets.aiogram_dialog.widgets.managed import ManagedWidgetAdapter


def mark_shift_day(manager: DialogManager) -> Optional[datetime.date]:
    ctx = manager.current_context()
    shift_date = (datetime.date.fromisoformat(ctx.dialog_data.get("shift_date"))
                  if ctx.dialog_data.get("shift_date") else datetime.date.today())
    return shift_date


async def on_process_result_shift_dialog(start_data: Data, result: Any, manager: DialogManager):
    pass


async def on_close_shift_dialog(result: Any, manager: DialogManager):
    pass


async def on_start_shift_dialog(start_data: Any, manager: DialogManager):
    pass


async def on_shift_list_page_changed(c: ChatEvent, adapter: ManagedScrollingGroupAdapter, manager: DialogManager):
    pass


async def on_employee_state_changed(event: ChatEvent,
                                    adapter: ManagedWidgetAdapter,
                                    manager: DialogManager,
                                    item_id: str):
    pass


async def on_success_enter_shift_duration(c: ChatEvent, widget: TextInput, manager: DialogManager, value):
    ctx = manager.current_context()
    session = manager.data.get("session")
    shift_date = datetime.date.fromisoformat(ctx.dialog_data.get("shift_date"))
    shift_number = int(ctx.dialog_data.get("shift_number"))
    shift_duration = float(value)
    await shift_update(session,
                       date=shift_date,
                       number=shift_number,
                       duration=shift_duration)
    ctx.dialog_data.update(shift_duration=value)
    await manager.switch_to(ShiftMenu.select_shift)
    # await c.delete()


async def on_success_enter_hours_worked(c: ChatEvent, widget: TextInput, manager: DialogManager, value):
    ctx = manager.current_context()
    session = manager.data.get("session")
    shift_date = datetime.date.fromisoformat(ctx.dialog_data.get("shift_date"))
    shift_number = int(ctx.dialog_data.get("shift_number"))
    employee_id = int(ctx.dialog_data.get("employee_id"))
    hours_worked = float(value)
    staff_for_add = [employee_id]
    await upsert_shift_staff(session,
                             shift_date=shift_date,
                             shift_number=shift_number,
                             hours_worked=hours_worked,
                             staff_for_add=staff_for_add,
                             staff_for_delete=None)
    await manager.switch_to(ShiftMenu.select_shift)
    await c.delete()


async def on_error_enter_hours_worked(c: ChatEvent, widget: TextInput, manager: DialogManager):
    pass
