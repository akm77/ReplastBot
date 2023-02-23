from aiogram.types import CallbackQuery

from . import states, constants
from ...models.erp_dict import DICT_FROM_NAME, DictType, dct_delete
from ...widgets.aiogram_dialog import DialogManager
from ...widgets.aiogram_dialog.widgets.kbd import Button, Select
from ...widgets.aiogram_dialog.widgets.managed import ManagedWidgetAdapter


async def on_select_dct(c: CallbackQuery, button: Button, manager: DialogManager):
    ctx = manager.current_context()
    ctx.dialog_data.pop("dct_item_id", None)
    ctx.dialog_data.update(dct=button.widget_id)

    dct = DICT_FROM_NAME.get(button.widget_id)
    if dct.hr_names.get("type") == DictType.SIMPLE:
        await manager.switch_to(states.DictMenuStates.show_simple_dct)


async def on_new_dct_item(c: CallbackQuery, button: Button, manager: DialogManager):
    ctx = manager.current_context()
    ctx.dialog_data.pop("dct_item_id", None)
    ctx.dialog_data.update(dct_edit_mode=constants.DctEditMode.NEW_RECORD)
    await manager.switch_to(states.DictMenuStates.edit_dct_item)


async def on_edit_dct_item(c: CallbackQuery, button: Button, manager: DialogManager):
    ctx = manager.current_context()
    ctx.dialog_data.update(dct_edit_mode=constants.DctEditMode.UPDATE_RECORD)
    await manager.switch_to(states.DictMenuStates.edit_dct_item)


async def on_delete_dct_item(c: CallbackQuery, button: Button, manager: DialogManager):
    ctx = manager.current_context()
    session = manager.data.get("session")
    dct = DICT_FROM_NAME.get(ctx.dialog_data.get("dct"))
    item_id = int(i) if (i := ctx.dialog_data.get("dct_item_id")) else 0
    await dct_delete(Session=session, table_class=dct, id=item_id)
    if dct.hr_names.get("type") == DictType.SIMPLE:
        await manager.switch_to(states.DictMenuStates.show_simple_dct)


async def on_dct_item_selected(c: CallbackQuery, widget: ManagedWidgetAdapter[Select], manager: DialogManager,
                               item_id: str):
    ctx = manager.current_context()
    ctx.dialog_data.update(dct_item_id=item_id)
    await manager.switch_to(states.DictMenuStates.show_dct_item)
