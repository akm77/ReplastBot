import datetime
import logging
from datetime import date
from typing import Any

from aiogram.types import CallbackQuery

from . import constants
from .states import ShiftMenu
from ...config import Config
from ...models.erp_shift import get_shift_row_number_on_date, upsert_shift_staff, shift_create
from ...widgets.aiogram_dialog import DialogManager
from ...widgets.aiogram_dialog.context.events import ChatEvent
from ...widgets.aiogram_dialog.widgets.kbd import ManagedScrollingGroupAdapter, Button, Select, ScrollingGroup, \
    Multiselect, Radio

logger = logging.getLogger(__name__)


async def on_click_calendar_back(c: CallbackQuery, widget: Button, manager: DialogManager):
    pass


async def on_date_selected(c: CallbackQuery, widget: Any,
                           manager: DialogManager, selected_date: date):
    ctx = manager.current_context()
    current_state = ctx.state
    session = manager.data.get("session")
    if current_state == ShiftMenu.select_shift_date:
        scrolling_group: ScrollingGroup = manager.dialog().find(constants.ShiftDialogId.SHIFT_LIST)
        try:
            result = (await get_shift_row_number_on_date(session, selected_date)).fetchall()
            page = result[0].row_number - 1 if result else 0
            await scrolling_group.set_page(c, page, manager)
        except Exception as e:
            logger.error("Error during write new shift. %r", e)
        await manager.switch_to(ShiftMenu.select_shift)
    elif current_state == ShiftMenu.select_new_shift_date:
        ctx.dialog_data.update(new_shift_date=selected_date.isoformat())
        await manager.switch_to(ShiftMenu.select_new_shift_number)


async def on_click_exit(c: ChatEvent, widget: Button, manager: DialogManager):
    await c.message.delete()


async def on_enter_page(c: ChatEvent, adapter: ManagedScrollingGroupAdapter, manager: DialogManager):
    await manager.switch_to(ShiftMenu.select_shift_date)


async def on_select_shift_duration(c: CallbackQuery, button: Button, manager: DialogManager):
    ctx = manager.current_context()
    await manager.switch_to(ShiftMenu.edit_shift_duration)


async def on_select_shift(c: CallbackQuery, button: Button, manager: DialogManager, shift_id: str):
    await manager.switch_to(ShiftMenu.edit_shift)


async def on_new_shift(c: CallbackQuery, widget: Any, manager: DialogManager, shift_date: date):
    pass


async def on_delete_shift(c: CallbackQuery, widget: Any, manager: DialogManager, shift_date: date, shift_number: int):
    pass


async def on_select_staff_member(c: CallbackQuery, widget: Select, manager: DialogManager,
                                 employee_id: str):
    ctx = manager.current_context()
    if int(employee_id) < 0:
        await manager.switch_to(ShiftMenu.select_staff)
        return
    else:
        ctx.dialog_data.update(employee_id=employee_id)
        await manager.switch_to(ShiftMenu.enter_hours_worked)


async def on_select_activity(c: CallbackQuery, widget: Any, manager: DialogManager,
                             activity_id):
    pass


async def on_select_material(c: CallbackQuery, widget: Any, manager: DialogManager,
                             material_id):
    ctx = manager.current_context()
    pass


async def on_select_product(c: CallbackQuery, widget: Any, manager: DialogManager,
                            product_id):
    pass


async def on_select_employee(c: CallbackQuery, select: Multiselect,
                             manager: DialogManager, item_id: str):
    ctx = manager.current_context()
    current_shift_staff = list(map(str, ctx.widget_data.get("current_shift_staff")))
    if select.is_checked(item_id, manager) and item_id in current_shift_staff:
        current_shift_staff.remove(item_id)
        ctx.widget_data.update(current_shift_staff=current_shift_staff)
    pass


async def on_cancel_button_click(c: CallbackQuery, button: Button, manager: DialogManager):
    ctx = manager.current_context()
    current_state = ctx.state
    if current_state == ShiftMenu.select_staff:
        employee_ms: Multiselect = manager.dialog().find(constants.ShiftDialogId.SELECT_SHIFT_STAFF)
        if ctx.widget_data.get("current_shift_staff"):
            ctx.widget_data.pop("current_shift_staff")
        await employee_ms.reset_checked(event=c, manager=manager)
    elif current_state == ShiftMenu.edit_shift:
        ctx.widget_data.pop(constants.ShiftDialogId.SHIFT_NUMBER_SELECT)
    elif current_state == ShiftMenu.select_new_shift_number:
        ctx.widget_data.pop(constants.ShiftDialogId.SHIFT_NUMBER_SELECT)


async def on_save_button_click(c: CallbackQuery, button: Button, manager: DialogManager):
    ctx = manager.current_context()
    current_state = ctx.state
    shift_date = ctx.dialog_data.get("shift_date")
    shift_number = ctx.dialog_data.get("shift_number")
    session = manager.data.get("session")
    config: Config = manager.data.get("config")
    if current_state == ShiftMenu.select_staff:
        employee_ms: Multiselect = manager.dialog().find(constants.ShiftDialogId.SELECT_SHIFT_STAFF)
        start_shift_staff = set(map(int, ctx.widget_data.get("start_shift_staff")))
        result_shift_staff = set(map(int, ctx.widget_data.get(constants.ShiftDialogId.SELECT_SHIFT_STAFF)))
        staff_for_add = result_shift_staff - start_shift_staff
        staff_for_delete = start_shift_staff - result_shift_staff
        if ctx.widget_data.get("current_shift_staff"):
            ctx.widget_data.pop("current_shift_staff")
        await employee_ms.reset_checked(event=c, manager=manager)
        await upsert_shift_staff(session,
                                 shift_date=datetime.date.fromisoformat(shift_date),
                                 shift_number=shift_number,
                                 hours_worked=config.misc.shift_duration,
                                 staff_for_add=staff_for_add,
                                 staff_for_delete=staff_for_delete)
    elif current_state == ShiftMenu.edit_shift:
        ctx.widget_data.pop(constants.ShiftDialogId.SHIFT_NUMBER_SELECT)
    elif current_state == ShiftMenu.select_new_shift_number:
        shift_date = ctx.dialog_data.get("new_shift_date")
        shift_number = int(ctx.widget_data.get(constants.ShiftDialogId.SHIFT_NUMBER_SELECT))
        ctx.widget_data.pop(constants.ShiftDialogId.SHIFT_NUMBER_SELECT)
        try:
            new_shift = await shift_create(session,
                                           date=datetime.date.fromisoformat(shift_date),
                                           number=shift_number,
                                           duration=config.misc.shift_duration)
            scrolling_group: ScrollingGroup = manager.dialog().find(constants.ShiftDialogId.SHIFT_LIST)
            result = (await get_shift_row_number_on_date(session, new_shift.date)).fetchall()
            page = result[shift_number - 1].row_number - 1 if result else 0
            await scrolling_group.set_page(c, page, manager)
        except Exception as e:
            logger.error("Error during write new shift. %r", e)

