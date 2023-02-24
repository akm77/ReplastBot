import logging

from . import constants, states
from ...models.erp_dict import DICT_FROM_NAME, dct_update, DictType, dct_create
from ...widgets.aiogram_dialog import ChatEvent, DialogManager
from ...widgets.aiogram_dialog.widgets.input import TextInput
from ...widgets.aiogram_dialog.widgets.managed import ManagedWidgetAdapter

logger = logging.getLogger(__name__)


async def dct_item_state_changed(event: ChatEvent,
                                 adapter: ManagedWidgetAdapter,
                                 manager: DialogManager):
    ctx = manager.current_context()
    session = manager.data.get("session")
    dct_item_state = ctx.widget_data.get(constants.DctMenuIds.DCT_ITEM_STATE)
    item_id = int(i) if (i := ctx.dialog_data.get("dct_item_id")) else 0
    dct = DICT_FROM_NAME.get(ctx.dialog_data.get("dct"))
    await dct_update(Session=session,
                     table_class=dct,
                     id=item_id,
                     is_active=dct_item_state)


async def on_success_enter_dct_item(c: ChatEvent, widget: TextInput, manager: DialogManager, value):
    ctx = manager.current_context()
    session = manager.data.get("session")
    dct = DICT_FROM_NAME.get(ctx.dialog_data.get("dct"))
    item_id = int(i) if (i := ctx.dialog_data.get("dct_item_id")) else 0
    if dct.hr_names.get("type") == DictType.SIMPLE:
        name, *tail = value.split("*")
        comment = "".join(tail) if len(tail) else None
        if item_id:
            try:
                ctx.dialog_data.pop("dct_item_id", None)
                await dct_update(Session=session,
                                 table_class=dct,
                                 id=item_id,
                                 name=name,
                                 comment=comment)
            except Exception as e:
                logger.error("Error occurred while updating dictionary %s. %r", ctx.dialog_data.get("dct"), e)
        else:
            try:
                await dct_create(Session=session,
                                 table_class=dct,
                                 name=name,
                                 comment=comment)
            except Exception as e:
                logger.error("Error occurred while creating new record in dictionary %s. %r",
                             ctx.dialog_data.get("dct"), e)
    ctx.dialog_data.pop("dct_edit_mode", None)
    await manager.switch_to(states.DictMenuStates.show_dct)


async def on_error_enter_dct_item(c: ChatEvent, widget: TextInput, manager: DialogManager):
    ctx = manager.current_context()
    ctx.dialog_data.pop("dct_item_id", None)
    ctx.dialog_data.pop("dct_edit_mode", None)
    await manager.switch_to(states.DictMenuStates.show_dct)
