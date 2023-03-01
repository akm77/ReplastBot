import logging

from . import constants, states
from ...models.erp_dict import DICT_FROM_NAME, dct_list, DictType, dct_read
from ...widgets.aiogram_dialog import DialogManager

logger = logging.getLogger(__name__)


async def get_dct_items(dialog_manager: DialogManager, **middleware_data):
    session = middleware_data.get('session')
    ctx = dialog_manager.current_context()
    dct_name = ctx.dialog_data.get("dct")
    dct_action = "Просмотр справочника"
    if ctx.state == states.DictMenuStates.select_dct_item:
        dct_name = ctx.dialog_data.get("dct_lookup_name")
        dct_action = "Выберите из справчоника"

    dct = DICT_FROM_NAME.get(dct_name)
    joined_load = None
    if dct_name == "ERPMaterial":
        joined_load = dct.material_type
    elif dct_name == "ERPProduct":
        joined_load = dct.product_type
    db_dct_items = await dct_list(Session=session,
                                  table_class=dct,
                                  joined_load=joined_load,
                                  order_by_name=True)
    if dct_name == "ERPMaterial":
        items = [(f"{item.name} [{item.material_type.name}], ♻️ {item.impurity}% "
                  f"{'(' + item.comment + ')' if item.comment else ''} "
                  f"{'🔔' if item.is_active else '🔕'}",
                  item.id) for item in db_dct_items]

    elif dct_name == "ERPProduct":
        items = [(f"{item.name} [{item.product_type.name}] "
                  f"{'(' + item.comment + ')' if item.comment else ''} "
                  f"{'🔔' if item.is_active else '🔕'}",
                  item.id) for item in db_dct_items]
    elif dct_name == "ERPUnitOfMeasurement":
        items = [(f"{item.code} => {item.name} "
                  f"{'(' + item.comment + ')' if item.comment else ''} "
                  f"{'🔔' if item.is_active else '🔕'}",
                  item.id) for item in db_dct_items]
    elif dct_name == "ERPContractor":
        items = [(f"{item.name} "
                  f"{'(' + item.comment + ')' if item.comment else ''} "
                  f"{'🚛' if item.is_provider else ''}"
                  f"{' 🛒' if item.is_buyer else ''}"
                  f"{'🔔' if item.is_active else '🔕'}",
                  item.id) for item in db_dct_items]
    else:
        items = [(f"{item.name} {'(' + item.comment + ')' if item.comment else ''} {'🔔' if item.is_active else '🔕'}",
                  item.id) for item in db_dct_items]
    ctx.dialog_data.pop("dct_lookup_name", None)
    return {"dct_action": dct_action,
            "dct_name": dct.hr_names.get("table_name"),
            "items": items}


async def get_dct_item(dialog_manager: DialogManager, **middleware_data):
    INSERT_PROMPT = ("*Создание новой записи*\nВведите название элемента и комментарий к нему.\n"
                     "Используйте * как разделитель названия и комментария👇")
    UPDATE_PROMPT = ("Введите название элемента и комментарий к нему.\n"
                     "Используйте * как разделитель названия и комментария👇")

    session = middleware_data.get('session')
    ctx = dialog_manager.current_context()
    dct_name = ctx.dialog_data.get("dct")
    dct = DICT_FROM_NAME.get(dct_name)
    item_id = int(i) if (i := ctx.dialog_data.get("dct_item_id")) else 0
    dct_item = ""
    joined_load = None
    if item_id:
        if dct_name == "ERPMaterial":
            joined_load = dct.material_type
        elif dct_name == "ERPProduct":
            joined_load = dct.product_type
        db_dct_item = await dct_read(Session=session, table_class=dct, id=item_id, joined_load=joined_load)
        ctx.widget_data[constants.DctMenuIds.DCT_ITEM_STATE] = db_dct_item.is_active if db_dct_item else False
        try:
            dct_item = (f"#{db_dct_item.id} {db_dct_item.name} "
                        f"{'(' + db_dct_item.comment + ')' if db_dct_item.comment else ''} "
                        f"{'🔔' if db_dct_item.is_active else '🔕'}\n")
            if dct_name == "ERPMaterial":
                dct_item += f"Тип: {db_dct_item.material_type.name}\n"
                dct_item += f"Примеси: {db_dct_item.impurity}%\n"
            elif dct_name == "ERPProduct":
                dct_item += f"Тип: {db_dct_item.material_type.name}"
            elif dct_name == "ERPContractor":
                ctx.widget_data[constants.DctMenuIds.IS_PROVIDER_STATE] = db_dct_item.is_provider if db_dct_item else False
                ctx.widget_data[constants.DctMenuIds.IS_BUYER_STATE] = db_dct_item.is_buyer if db_dct_item else False
                dct_item += f"Поставщик: {'🚛' if db_dct_item.is_provider else ''}\n"
                dct_item += f"Покупатель: {' 🛒' if db_dct_item.is_buyer else ''}\n"

        except Exception as e:
            logger.error("Error while construct dictionary item. %r", e)
        if ctx.state == states.DictMenuStates.edit_dct_item:
            dct_item += UPDATE_PROMPT
    else:
        if dct_name in ("ERPMaterial", "ERPProduct"):
            item_id = int(ctx.dialog_data.get("lookup_item_id"))
            db_dct_item = await dct_read(Session=session, table_class=dct.hr_names["lookup"], id=item_id)
            dct_item = f"Тип: {db_dct_item.name}\n"
        dct_item += INSERT_PROMPT
    return {"dct_item": dct_item}
