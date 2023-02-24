from . import constants
from ...models.erp_dict import DICT_FROM_NAME, dct_list, DictType, dct_read
from ...widgets.aiogram_dialog import DialogManager


async def get_dct_items(dialog_manager: DialogManager, **middleware_data):
    session = middleware_data.get('session')
    ctx = dialog_manager.current_context()
    dct_name = ctx.dialog_data.get("dct")
    dct = DICT_FROM_NAME.get(dct_name)
    joined_load = None
    if dct_name == "ERPContractor":
        joined_load = dct.city
    elif dct_name == "ERPMaterial":
        joined_load = dct.material_type
    elif dct_name == "ERPProduct":
        joined_load = dct.product_type
    db_dct_items = await dct_list(Session=session,
                                  table_class=dct,
                                  joined_load=joined_load,
                                  order_by_name=True)
    if dct_name == "ERPContractor":
        items = [(f"{item.name} [{item.city.name}] {'(' + item.comment + ')' if item.comment else ''} "
                  f"{'🔔' if item.is_active else '🔕'}",
                  item.id) for item in db_dct_items]

    elif dct_name == "ERPMaterial":
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
    else:
        items = [(f"{item.name} {'(' + item.comment + ')' if item.comment else ''} {'🔔' if item.is_active else '🔕'}",
                  item.id) for item in db_dct_items]
    return {"dct_name": dct.hr_names.get("table_name"),
            "items": items}


async def get_dct_item(dialog_manager: DialogManager, **middleware_data):
    INSERT_PROMPT = ("*Создание новой записи*\nВведите название элемента и комментарий к нему.\n"
                     "Используйте * как разделитель названия и комментария👇")
    UPDATE_PROMPT = ("Введите название элемента и комментарий к нему.\n"
                     "Используйте * как разделитель названия и комментария👇")

    session = middleware_data.get('session')
    ctx = dialog_manager.current_context()
    ctx.widget_data.update()
    dct_name = ctx.dialog_data.get("dct")
    dct = DICT_FROM_NAME.get(dct_name)
    item_id = int(i) if (i := ctx.dialog_data.get("dct_item_id")) else 0
    dct_item = ""
    if item_id and dct.hr_names.get("type") == DictType.SIMPLE:
        db_dct_item = await dct_read(Session=session, table_class=dct, id=item_id)
        ctx.widget_data[constants.DctMenuIds.DCT_ITEM_STATE] = db_dct_item.is_active
        dct_item = (f"#{db_dct_item.id} {db_dct_item.name} "
                    f"{'(' + db_dct_item.comment + ')' if db_dct_item.comment else ''} "
                    f"{'🔔' if db_dct_item.is_active else '🔕'}\n")
    elif item_id and dct.hr_names.get("type") == DictType.COMPLEX:
        joined_load = None
        if dct_name == "ERPContractor":
            joined_load = dct.city
        elif dct_name == "ERPMaterial":
            joined_load = dct.material_type
        elif dct_name == "ERPProduct":
            joined_load = dct.product_type
        db_dct_item = await dct_read(Session=session, table_class=dct, id=item_id, joined_load=joined_load)
    elif not item_id and dct.hr_names.get("type") == DictType.SIMPLE:
        dct_item = INSERT_PROMPT
    elif not item_id and dct.hr_names.get("type") == DictType.COMPLEX:
        pass
    if ctx.dialog_data.get("dct_edit_mode"):
        dct_item += UPDATE_PROMPT
    return {"dct_item": dct_item}
