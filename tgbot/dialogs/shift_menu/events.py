import datetime
import logging
from typing import Any, Optional

from .states import ShiftMenu
from ...models.erp_shift import upsert_shift_staff, shift_update, set_shift_activity_comment, material_intake_create, \
    shift_product_line_create
from ...widgets.aiogram_dialog import DialogManager
from ...widgets.aiogram_dialog.context.events import ChatEvent, Data
from ...widgets.aiogram_dialog.widgets.input import TextInput
from ...widgets.aiogram_dialog.widgets.kbd import ManagedScrollingGroupAdapter
from ...widgets.aiogram_dialog.widgets.managed import ManagedWidgetAdapter

logger = logging.getLogger(__name__)


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
    await c.delete()


async def on_error_enter_shift_duration(c: ChatEvent, widget: TextInput, manager: DialogManager):
    ctx = manager.current_context()
    ctx.dialog_data.pop("shift_date", None)
    ctx.dialog_data.pop("shift_number", None)
    await manager.switch_to(ShiftMenu.select_shift)
    await c.delete()


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
    ctx = manager.current_context()
    ctx.dialog_data.pop("shift_date", None)
    ctx.dialog_data.pop("shift_number", None)
    ctx.dialog_data.pop("employee_id", None)
    await manager.switch_to(ShiftMenu.select_shift)
    await c.delete()


async def on_success_enter_activity_comment(c: ChatEvent, widget: TextInput, manager: DialogManager, value):
    ctx = manager.current_context()
    session = manager.data.get("session")
    shift_date = datetime.date.fromisoformat(ctx.dialog_data.get("shift_date"))
    shift_number = int(ctx.dialog_data.get("shift_number"))
    line_number = int(ctx.dialog_data.get("activity_line_number"))
    comment = value if value != "*-" else None
    await set_shift_activity_comment(session,
                                     shift_date=shift_date,
                                     shift_number=shift_number,
                                     line_number=line_number,
                                     comment=comment)
    await manager.switch_to(ShiftMenu.select_shift)
    await c.delete()


async def on_error_enter_activity_comment(c: ChatEvent, widget: TextInput, manager: DialogManager):
    ctx = manager.current_context()
    ctx.dialog_data.pop("shift_date", None)
    ctx.dialog_data.pop("shift_number", None)
    ctx.dialog_data.pop("activity_line_number", None)
    await manager.switch_to(ShiftMenu.select_shift)
    await c.delete()


async def on_success_enter_material_quantity(c: ChatEvent, widget: TextInput, manager: DialogManager, value):
    session = manager.data.get("session")
    ctx = manager.current_context()
    shift_date = ctx.dialog_data.get("shift_date")
    shift_number = int(ctx.dialog_data.get("shift_number"))
    material_id = int(n) if (n := ctx.dialog_data.get("material_id")) else 0
    material_line_number = int(n) if (n := ctx.dialog_data.get("material_line_number")) else 0
    try:
        if ctx.dialog_data.get("material_id"):
            ctx.dialog_data.pop("material_id")
        if ctx.dialog_data.get("material_line_number"):
            ctx.dialog_data.pop("material_line_number")
        quantity, *tail = value.split()
        comment = "".join(tail)
        quantity = float(quantity)
        if material_line_number <= 0:
            await material_intake_create(Session=session,
                                         shift_date=datetime.date.fromisoformat(shift_date),
                                         shift_number=shift_number,
                                         material_id=material_id,
                                         quantity=quantity,
                                         comment=comment)
    except Exception as e:
        logger.error("Error occurred while creating material intake. %r", e)
    await manager.switch_to(ShiftMenu.select_shift)
    await c.delete()


async def on_error_enter_material_quantity(c: ChatEvent, widget: TextInput, manager: DialogManager, value):
    ctx = manager.current_context()
    ctx.dialog_data.pop("shift_date", None)
    ctx.dialog_data.pop("shift_number", None)
    ctx.dialog_data.pop("material_id", None)
    ctx.dialog_data.pop("material_line_number", None)
    await manager.switch_to(ShiftMenu.select_shift)
    await c.delete()


async def on_success_enter_product_bag_quantity(c: ChatEvent, widget: TextInput, manager: DialogManager, value):
    session = manager.data.get("session")
    ctx = manager.current_context()
    shift_date = ctx.dialog_data.get("shift_date")
    shift_number = int(ctx.dialog_data.get("shift_number"))
    product_id = int(n) if (n := ctx.dialog_data.get("product_id")) else 0
    product_line_number = int(n) if (n := ctx.dialog_data.get("product_line_number")) else 0
    try:
        if ctx.dialog_data.get("product_id"):
            ctx.dialog_data.pop("product_id")
        if ctx.dialog_data.get("product_line_number"):
            ctx.dialog_data.pop("product_line_number")
        batch_number, quantity, *tail = value.split()
        comment = "".join(tail)
        batch_number = int(batch_number)
        quantity = float(quantity)
        if product_line_number <= 0:
            await shift_product_line_create(Session=session,
                                            shift_date=datetime.date.fromisoformat(shift_date),
                                            shift_number=shift_number,
                                            batch_number=batch_number,
                                            product_id=product_id,
                                            quantity=quantity,
                                            comment=comment)
    except Exception as e:
        logger.error("Error occurred while creating product line. %r", e)
    await manager.switch_to(ShiftMenu.select_shift)
    await c.delete()


async def on_error_enter_product_bag_quantity(c: ChatEvent, widget: TextInput, manager: DialogManager, value):
    ctx = manager.current_context()
    ctx.dialog_data.pop("shift_date", None)
    ctx.dialog_data.pop("shift_number", None)
    ctx.dialog_data.pop("product_id", None)
    ctx.dialog_data.pop("product_line_number", None)
    await manager.switch_to(ShiftMenu.select_shift)
    await c.delete()

