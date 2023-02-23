from . import constants
from ...models.erp_dict import DICT_FROM_NAME, dct_list, DictType, dct_read
from ...widgets.aiogram_dialog import DialogManager


async def get_simple_dct_items(dialog_manager: DialogManager, **middleware_data):
    session = middleware_data.get('session')
    ctx = dialog_manager.current_context()
    dct = DICT_FROM_NAME.get(ctx.dialog_data.get("dct"))
    db_dct_items = await dct_list(Session=session,
                                  table_class=dct,
                                  order_by_name=True)
    items = [(f"{item.name} {'(' + item.comment + ')' if item.comment else ''} {'🔔' if item.is_active else '🔕'}",
              item.id) for item in db_dct_items]
    return {"dct_name": dct.hr_names.get("table_name"),
            "items": items}


async def get_dct_item(dialog_manager: DialogManager, **middleware_data):
    session = middleware_data.get('session')
    ctx = dialog_manager.current_context()
    ctx.widget_data.update()
    dct = DICT_FROM_NAME.get(ctx.dialog_data.get("dct"))
    item_id = int(i) if (i := ctx.dialog_data.get("dct_item_id")) else 0
    dct_item = ""
    if item_id and dct.hr_names.get("type") == DictType.SIMPLE:
        db_dct_item = await dct_read(Session=session, table_class=dct, id=item_id)
        ctx.widget_data[constants.DctMenuIds.DCT_ITEM_STATE] = db_dct_item.is_active
        dct_item = (f"#{db_dct_item.id} {db_dct_item.name} "
                    f"{'(' + db_dct_item.comment + ')' if db_dct_item.comment else ''} "
                    f"{'🔔' if db_dct_item.is_active else '🔕'}\n")
        if ctx.dialog_data.get("dct_edit_mode"):
            dct_item += ("Введите название элемента и комментарий к нему.\n"
                         "Используйте * как разделитель названия и комментария👇")

    elif item_id and dct.hr_names.get("type") == DictType.COMPLEX:
        pass
    elif not item_id and dct.hr_names.get("type") == DictType.SIMPLE:
        dct_item = ("*Создание новой записи*\nВведите название элемента и комментарий к нему.\n"
                    "Используйте * как разделитель названия и комментария👇")
    elif not item_id and dct.hr_names.get("type") == DictType.COMPLEX:
        pass
    return {"dct_item": dct_item}
