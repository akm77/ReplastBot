import datetime
import logging
from datetime import date
from typing import Any

from aiogram.types import CallbackQuery

from . import constants
from .states import ShiftMenu
from ...config import Config
from ...models.erp_shift import get_shift_row_number_on_date, upsert_shift_staff, shift_create, update_shift_activities, \
    shift_read
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


async def on_send_to_journal(c: ChatEvent, widget: Button, manager: DialogManager):
    state = {'ok': '✅', 'todo': '‼️', 'back': '📛'}

    ctx = manager.current_context()
    session = manager.data.get("session")
    config: Config = manager.data.get("config")
    journal_chat = config.misc.journal_chat
    shift_date = datetime.date.fromisoformat(ctx.dialog_data.get("shift_date"))
    shift_number = ctx.dialog_data.get("shift_number")
    shift = await shift_read(session,
                             date=shift_date,
                             number=int(shift_number))
    shift_text = [f"{shift.date: %d.%m.%Y} смена: {shift.number} ({shift.duration} ч)\n{'-' * 30}"]
    shift_text += [f"{'=' * 5} ПЕРСОНАЛ {'=' * 5}"]
    shift_text += [f"#{i} {employee.employee.name} - {employee.hours_worked} ч"
                   for i, employee in enumerate(shift.shift_staff, start=1)]
    shift_text += [f"{'=' * 5} РАБОТЫ {'=' * 5}"]
    shift_text += [f"#{activity.line_number} {activity.activity.name} {'(' + activity.comment + ')' if activity.comment else ''}"
                   for activity in shift.shift_activities]
    shift_text += [f"{'=' * 5} ПРОДУКЦИЯ {'=' * 5}"]
    shift_text += [f"#{bn.batch_number if (bn := product.product_butch_number) else ''} "
                   f"{product.product.name} ({product.product.product_type.name})- "
                   f"{product.quantity} {product.product.uom_code} "
                   f"{state[product.state]}"
                   f" {'(' + product.comment + ')' if product.comment else ''}"
                   for product in shift.shift_products]
    shift_text += [f"{'=' * 5} СЫРЬЁ {'=' * 5}"]
    shift_text += [f"#{material.line_number} {material.material.name} "
                   f"({material.material.material_type.name}) - "
                   f"{material.quantity} {material.material.uom_code} "
                   f"{'✅' if material.is_processed else '‼️'}"
                   f" {'(' + material.comment + ')' if material.comment else ''}"
                   for material in shift.shift_materials]
    message_text = "\n".join(shift_text)
    await c.message.bot.send_message(chat_id=journal_chat, text=message_text)


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


async def on_select_shift_object(c: CallbackQuery, widget: Select, manager: DialogManager,
                                 complex_item_id: str):
    ctx = manager.current_context()
    item_id, dictionary, state = complex_item_id.split("_")
    ctx.dialog_data.update(dictionary=dictionary)
    if item_id == "-1" and dictionary in [constants.SelectDictionary.Employee, constants.SelectDictionary.Activity]:
        await manager.switch_to(ShiftMenu.multi_select_from_dct)
    elif item_id == "-1" and dictionary in [constants.SelectDictionary.Material, constants.SelectDictionary.Product]:
        await manager.switch_to(ShiftMenu.select_from_dct)
    elif dictionary == constants.SelectDictionary.Employee:
        ctx.dialog_data.update(employee_id=item_id)
        await manager.switch_to(ShiftMenu.enter_hours_worked)
    elif dictionary == constants.SelectDictionary.Activity:
        ctx.dialog_data.update(activity_line_number=item_id)
        await manager.switch_to(ShiftMenu.enter_activity_comment)
    elif dictionary == constants.SelectDictionary.Material:
        ctx.dialog_data.update(material_line_number=item_id)
    elif dictionary == constants.SelectDictionary.Product:
        ctx.dialog_data.update(product_line_number=item_id)


async def on_select_shift_activity(c: CallbackQuery, widget: Any, manager: DialogManager,
                                   line_number):
    pass


async def on_select_shift_material(c: CallbackQuery, widget: Any, manager: DialogManager,
                                   material_id):
    ctx = manager.current_context()
    pass


async def on_select_shift_product(c: CallbackQuery, widget: Any, manager: DialogManager,
                                  product_id):
    pass


async def on_multi_select_dct_item(c: CallbackQuery, select: Multiselect,
                                   manager: DialogManager, item_id: str):
    ctx = manager.current_context()
    current_items_id = list(map(str, ctx.widget_data.get("current_items_id")))
    if select.is_checked(item_id, manager) and item_id in current_items_id:
        current_items_id.remove(item_id)
        ctx.widget_data.update(current_items_id=current_items_id)


async def on_select_dct_item(c: CallbackQuery, select: Select,
                             manager: DialogManager, item_id: str):
    ctx = manager.current_context()
    dictionary = ctx.dialog_data.get("dictionary")
    if dictionary == constants.SelectDictionary.Material:
        ctx.dialog_data.update(material_id=item_id)
        await manager.switch_to(ShiftMenu.enter_material_quantity)
    elif dictionary == constants.SelectDictionary.Product:
        ctx.dialog_data.update(product_id=item_id)
        await manager.switch_to(ShiftMenu.enter_product_bag_quantity)


async def on_select_material(c: CallbackQuery, select: Multiselect,
                             manager: DialogManager, item_id: str):
    pass


async def on_select_product(c: CallbackQuery, select: Multiselect,
                            manager: DialogManager, item_id: str):
    pass


async def on_cancel_button_click(c: CallbackQuery, button: Button, manager: DialogManager):
    ctx = manager.current_context()
    current_state = ctx.state
    if current_state == ShiftMenu.edit_shift:
        ctx.widget_data.pop(constants.ShiftDialogId.SHIFT_NUMBER_SELECT)
    elif current_state == ShiftMenu.select_new_shift_number:
        ctx.widget_data.pop(constants.ShiftDialogId.SHIFT_NUMBER_SELECT)
    elif current_state == ShiftMenu.multi_select_from_dct:
        ctx.widget_data.pop("start_items_id")
        ctx.widget_data.pop("current_items_id")
        ctx.widget_data.pop(constants.ShiftDialogId.MULTI_SELECT_FROM_DCT)


async def on_save_button_click(c: CallbackQuery, button: Button, manager: DialogManager):
    ctx = manager.current_context()
    current_state = ctx.state
    shift_date = ctx.dialog_data.get("shift_date")
    shift_number = ctx.dialog_data.get("shift_number")
    session = manager.data.get("session")
    config: Config = manager.data.get("config")
    if current_state == ShiftMenu.multi_select_from_dct:
        dictionary = ctx.dialog_data.get("dictionary")
        ms: Multiselect = manager.dialog().find(constants.ShiftDialogId.MULTI_SELECT_FROM_DCT)
        start_items_id = set(map(int, ctx.widget_data.get("start_items_id")))
        result_items_id = set(map(int, ctx.widget_data.get(constants.ShiftDialogId.MULTI_SELECT_FROM_DCT)))
        items_for_add = result_items_id - start_items_id
        items_for_delete = start_items_id - result_items_id
        ctx.widget_data.pop("start_items_id")
        ctx.widget_data.pop("current_items_id")
        await ms.reset_checked(event=c, manager=manager)
        if dictionary == constants.SelectDictionary.Employee:
            await upsert_shift_staff(session,
                                     shift_date=datetime.date.fromisoformat(shift_date),
                                     shift_number=shift_number,
                                     hours_worked=config.misc.shift_duration,
                                     staff_for_add=items_for_add,
                                     staff_for_delete=items_for_delete)
        elif dictionary == constants.SelectDictionary.Activity:
            await update_shift_activities(session,
                                          shift_date=datetime.date.fromisoformat(shift_date),
                                          shift_number=shift_number,
                                          items_for_add=sorted(list(items_for_add)),
                                          items_for_delete=list(items_for_delete))
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
