import logging

from . import constants, states
from ...models.erp_dict import DICT_FROM_NAME, dct_update, dct_create
from ...widgets.aiogram_dialog import ChatEvent, DialogManager
from ...widgets.aiogram_dialog.context.context import Context
from ...widgets.aiogram_dialog.widgets.input import TextInput
from ...widgets.aiogram_dialog.widgets.managed import ManagedWidgetAdapter

logger = logging.getLogger(__name__)


async def dct_item_state_changed(event: ChatEvent,
                                 adapter: ManagedWidgetAdapter,
                                 manager: DialogManager):
    ctx = manager.current_context()
    session = manager.data.get("session")
    dct_item_state = ctx.widget_data.get(constants.DctMenuIds.DCT_ITEM_STATE)
    values = {"is_active": dct_item_state}
    item_id = int(i) if (i := ctx.dialog_data.get("dct_item_id")) else 0
    dct_name = ctx.dialog_data.get("dct")
    dct = DICT_FROM_NAME.get(dct_name)
    if dct_name == "ERPContractor":
        is_provider = ctx.widget_data.get(constants.DctMenuIds.IS_PROVIDER_STATE)
        is_buyer = ctx.widget_data.get(constants.DctMenuIds.IS_BUYER_STATE)
        values.update(is_provider=is_provider, is_buyer=is_buyer)
    await dct_update(Session=session,
                     table_class=dct,
                     id=item_id,
                     **values)


def clear_tmp_dialog_data(ctx: Context):
    ctx.dialog_data.pop("dct_edit_mode", None)
    ctx.dialog_data.pop("lookup_item_id", None)
    ctx.dialog_data.pop("dct_lookup_name", None)
    ctx.dialog_data.pop("dct_item_id", None)
    ctx.dialog_data.pop("content_type", None)


async def on_success_enter_dct_item(c: ChatEvent, widget: TextInput, manager: DialogManager, value):
    ctx = manager.current_context()
    session = manager.data.get("session")
    dct_name = ctx.dialog_data.get("dct")
    dct = DICT_FROM_NAME.get(dct_name)
    values = {}
    item_id = int(i) if (i := ctx.dialog_data.get("dct_item_id")) else 0
    content_type = ctx.dialog_data.get("content_type") if ctx.dialog_data.get("content_type") else "text"
    if content_type == "text":
        name, *tail = value.split("*")
        comment = "".join(tail) if len(tail) else None
        values["name"] = name
        values["comment"] = comment
        if dct_name == "ERPUnitOfMeasurement":
            code, *uom_name = values["name"].split()
            values["code"] = code
            values["name"] = "".join(uom_name) if len(uom_name) else code
    elif content_type == "float":
        try:
            value = float(value)
        except ValueError as e:
            logger.error("Error occurred while get float value for dictionary %s. %r", ctx.dialog_data.get("dct"), e)
            await manager.switch_to(states.DictMenuStates.show_dct)
            return
        if dct_name == "ERPMaterial":
            values["impurity"] = value

    if item_id:
        try:
            ctx.dialog_data.pop("dct_item_id", None)
            await dct_update(Session=session,
                             table_class=dct,
                             id=item_id,
                             **values)
        except Exception as e:
            logger.error("Error occurred while updating dictionary %s. %r", ctx.dialog_data.get("dct"), e)
    else:
        if dct_name == "ERPMaterial":
            values["material_type_id"] = int(ctx.dialog_data.get("lookup_item_id"))
        elif dct_name == "ERPProduct":
            values["product_type_id"] = int(ctx.dialog_data.get("lookup_item_id"))
        try:
            await dct_create(Session=session,
                             table_class=dct,
                             **values)
        except Exception as e:
            logger.error("Error occurred while creating new record in dictionary %s. %r",
                         ctx.dialog_data.get("dct"), e)

    clear_tmp_dialog_data(ctx)
    await manager.switch_to(states.DictMenuStates.show_dct)


async def on_error_enter_dct_item(c: ChatEvent, widget: TextInput, manager: DialogManager):
    ctx = manager.current_context()
    clear_tmp_dialog_data(ctx)
    await manager.switch_to(states.DictMenuStates.show_dct)
