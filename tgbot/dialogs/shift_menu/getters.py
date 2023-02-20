import datetime
import logging
from typing import Optional, List

from . import constants
from ...models.erp_dict import ERPEmployee, dct_list, ERPActivity, ERPMaterial, ERPProduct, dct_read
from ...models.erp_shift import ERPShift, shift_list_full, shift_read, get_shift_staff_member, select_day_shift_numbers, \
    read_shift_activity
from ...widgets.aiogram_dialog import DialogManager
from ...widgets.aiogram_dialog.widgets.kbd import Multiselect, Radio

logger = logging.getLogger(__name__)


def get_shift_staff_list(shift: ERPShift) -> Optional[List]:
    staff_button = [("<- ПЕРСОНАЛ ->", f"-1_{constants.SelectDictionary.Employee}_0")]
    return staff_button + [(f"{employee.employee.name} - {employee.hours_worked} ч",
                            f"{employee.employee_id}_{constants.SelectDictionary.Employee}_0")
                           for employee in shift.shift_staff]


def get_shift_activity_list(shift: ERPShift) -> Optional[List]:
    activity_button = [("<- РАБОТЫ ->", f"-1_{constants.SelectDictionary.Activity}_0")]
    return activity_button + [(f"{activity.activity.name} {'(' + activity.comment + ')' if activity.comment else ''}",
                               f"{activity.line_number}_{constants.SelectDictionary.Activity}_0")
                              for activity in shift.shift_activities]


def get_shift_material_list(shift: ERPShift) -> Optional[List]:
    material_button = [("<- СЫРЬЁ ->", f"-1_{constants.SelectDictionary.Material}_0")]
    return material_button + [(f"#{material.line_number} {material.material.name} "
                               f"({material.material.material_type.name}) - "
                               f"{material.quantity} {material.material.uom_code} "
                               f"{'✅' if material.is_processed else '‼️'}"
                               f" {'(' + material.comment + ')' if material.comment else ''}",
                               f"{material.line_number}_{constants.SelectDictionary.Material}_{material.is_processed}")
                              for material in shift.shift_materials]


def get_shift_product_list(shift: ERPShift) -> Optional[List]:
    state = {'ok': '✅', 'todo': '‼️', 'back': '📛'}
    product_button = [("<- ПРОДУКЦИЯ ->", f"-1_{constants.SelectDictionary.Product}_0")]
    return product_button + [(f"#{bn.batch_number if (bn := product.product_butch_number) else ''} "
                              f"{product.product.name} ({product.product.product_type.name})- "
                              f"{product.quantity} {product.product.uom_code} "
                              f"{state[product.state]}"
                              f" {'(' + product.comment + ')' if product.comment else ''}",
                              f"{product.line_number}_{constants.SelectDictionary.Product}_{product.state}")
                             for product in shift.shift_products]


async def get_shift_list(dialog_manager: DialogManager, **middleware_data):
    session = middleware_data.get('session')
    ctx = dialog_manager.current_context()

    db_shift_list = await shift_list_full(session, reverse=False)
    shift_list = [
        (f'{shift.date: %d.%m.%Y} смена: {shift.number} ({shift.duration} ч)',
         f'{shift.date}_{shift.number}_{shift.duration}')
        for shift in db_shift_list
    ]
    page = int(page) if (page := ctx.widget_data.get(constants.ShiftDialogId.SHIFT_LIST)) else 0
    shift_date, shift_number, shift_duration = shift_list[page][1].split("_")
    ctx.dialog_data.update(shift_date=shift_date, shift_number=shift_number, shift_duration=shift_duration)
    shift = await shift_read(session,
                             date=datetime.date.fromisoformat(shift_date),
                             number=int(shift_number))
    shift_staff = []
    shift_activity = []
    shift_material = []
    shift_product = []
    if shift:
        shift_staff = get_shift_staff_list(shift)
        shift_activity = get_shift_activity_list(shift)
        shift_material = get_shift_material_list(shift)
        shift_product = get_shift_product_list(shift)

    data = {
        "shift_list": shift_list,
        "shift_staff": shift_staff,
        "shift_activity": shift_activity,
        "shift_material": shift_material,
        "shift_product": shift_product
    }
    return data


async def get_selected_shift(dialog_manager: DialogManager, **middleware_data):
    ctx = dialog_manager.current_context()
    shift_date = datetime.date.fromisoformat(ctx.dialog_data.get("shift_date"))
    shift_number = ctx.dialog_data.get("shift_number")
    shift_duration = float(ctx.dialog_data.get("shift_duration"))
    return {"shift_date": shift_date,
            "shift_number": shift_number,
            "shift_duration": shift_duration
            }


async def get_new_shift(dialog_manager: DialogManager, **middleware_data):
    session = middleware_data.get('session')
    ctx = dialog_manager.current_context()

    shift_date = datetime.date.fromisoformat(ctx.dialog_data.get("shift_date"))
    shift_number = ctx.dialog_data.get("shift_number")
    shift_duration = float(ctx.dialog_data.get("shift_duration"))
    new_shift_date = datetime.date.fromisoformat(ctx.dialog_data.get("new_shift_date")
                                                 ) if ctx.dialog_data.get("new_shift_date") else datetime.date.today()

    db_day_shift_numbers = await select_day_shift_numbers(session, date=new_shift_date)
    day_shift_numbers = {1, 2, 3} - {shift.number for shift in db_day_shift_numbers}
    shift_numbers = sorted([(n, n) for n in day_shift_numbers])
    radio: Radio = dialog_manager.dialog().find(constants.ShiftDialogId.SHIFT_NUMBER_SELECT)
    if not radio.get_checked(dialog_manager):
        await radio.set_checked(event=dialog_manager.event,
                                item_id=str(shift_numbers[0][1]) if len(shift_numbers) else "1",
                                manager=dialog_manager)

    return {"shift_date": shift_date,
            "new_shift_date": new_shift_date,
            "shift_number": shift_number,
            "shift_numbers": shift_numbers,
            "shift_duration": shift_duration
            }


async def get_staff_employee(dialog_manager: DialogManager, **middleware_data):
    session = middleware_data.get('session')
    ctx = dialog_manager.current_context()
    shift_date = ctx.dialog_data.get("shift_date")
    shift_number = ctx.dialog_data.get("shift_number")
    employee_id = ctx.dialog_data.get("employee_id")
    try:
        employee = await get_shift_staff_member(Session=session,
                                                shift_date=datetime.date.fromisoformat(shift_date),
                                                shift_number=int(shift_number),
                                                employee_id=int(employee_id))
        employee_name = employee.employee.name
        employee_shift_date = employee.shift_date.strftime("%d.%m.%Y")
        employee_shift_number = employee.shift_number
        employee_hours_worked = employee.hours_worked
    except Exception as e:
        logger.info("Error querying shift staff. Date %s, number %s. %r", shift_date, shift_number, e)
        await dialog_manager.done()
        return

    return {"employee_name": employee_name,
            "employee_shift_date": employee_shift_date,
            "employee_shift_number": employee_shift_number,
            "employee_hours_worked": employee_hours_worked}


async def multi_select_from_dct(dialog_manager: DialogManager, **middleware_data):
    ctx = dialog_manager.current_context()
    shift_date = ctx.dialog_data.get("shift_date")
    shift_number = ctx.dialog_data.get("shift_number")
    dictionary = ctx.dialog_data.get("dictionary")
    session = middleware_data.get('session')
    ms: Multiselect = dialog_manager.dialog().find(constants.ShiftDialogId.MULTI_SELECT_FROM_DCT)

    try:
        shift = await shift_read(session,
                                 date=datetime.date.fromisoformat(shift_date),
                                 number=int(shift_number))
    except Exception as e:
        logger.info("Error querying shift. Date %s, number %s. %r", shift_date, shift_number, e)
        await dialog_manager.done()
        return

    db_dct_list = []
    start_items_id = []
    if dictionary == constants.SelectDictionary.Employee:
        start_items_id = [str(employee.employee_id) for employee in shift.shift_staff]
        db_dct_list = await dct_list(Session=session, table_class=ERPEmployee)
    elif dictionary == constants.SelectDictionary.Activity:
        start_items_id = [str(activity.activity_id) for activity in shift.shift_activities]
        db_dct_list = await dct_list(Session=session, table_class=ERPActivity)

    current_items_id = c if (c := ctx.widget_data.get("current_items_id")
                             ) is not None else start_items_id
    ctx.widget_data.update(start_items_id=start_items_id)
    ctx.widget_data.update(current_items_id=current_items_id)

    items = [(item.name, item.id) for item in db_dct_list]
    _ = [(await ms.set_checked(event=dialog_manager.event,
                               item_id=str(item[1]),
                               checked=True,
                               manager=dialog_manager)) for item in items
         if str(item[1]) in current_items_id]

    return {"items": items}


async def select_from_dct(dialog_manager: DialogManager, **middleware_data):
    ctx = dialog_manager.current_context()
    dictionary = ctx.dialog_data.get("dictionary")
    session = middleware_data.get('session')
    items = []
    if dictionary == constants.SelectDictionary.Material:
        db_dct_list = await dct_list(Session=session, table_class=ERPMaterial, joined_load=ERPMaterial.material_type)
        items = [(f"{item.name} ({item.material_type.name})", item.id) for item in db_dct_list]
    elif dictionary == constants.SelectDictionary.Product:
        db_dct_list = await dct_list(Session=session, table_class=ERPProduct, joined_load=ERPProduct.product_type)
        items = [(f"{item.name} ({item.product_type.name})", item.id) for item in db_dct_list]
    return {"items": items}


async def get_shift_activity(dialog_manager: DialogManager, **middleware_data):
    session = middleware_data.get('session')
    ctx = dialog_manager.current_context()
    shift_date = ctx.dialog_data.get("shift_date")
    shift_number = int(ctx.dialog_data.get("shift_number"))
    shift_duration = float(ctx.dialog_data.get("shift_duration"))
    line_number = int(ctx.dialog_data.get("activity_line_number"))
    activity = await read_shift_activity(Session=session,
                                         shift_date=datetime.date.fromisoformat(shift_date),
                                         shift_number=shift_number,
                                         line_number=line_number)
    return {"shift_date": shift_date,
            "shift_number": shift_number,
            "shift_duration": shift_duration,
            "activity_name": activity.activity.name,
            "activity_comment": activity.comment if activity.comment else ""}


async def get_shift_material_quantity(dialog_manager: DialogManager, **middleware_data):
    # Format("Текущая смена☞ дата: {shift_date} номер: {shift_number} время: {shift_duration} ч\n"
    #        "Сырье - {material_name}.\n"
    #        "👇Количество: {material_quantity}.👇"),
    session = middleware_data.get('session')
    ctx = dialog_manager.current_context()
    shift_date = ctx.dialog_data.get("shift_date")
    shift_number = int(ctx.dialog_data.get("shift_number"))
    shift_duration = float(ctx.dialog_data.get("shift_duration"))
    material_id = int(n) if (n := ctx.dialog_data.get("material_id")) else 0
    material_line_number = int(n) if (n := ctx.dialog_data.get("material_line_number")) else 0
    dct = {"shift_date": shift_date,
           "shift_number": shift_number,
           "shift_duration": shift_duration,
           "material_name": "",
           "material_quantity": 0}
    if material_line_number <= 0:
        material: ERPMaterial = await dct_read(session, ERPMaterial,
                                               joined_load=ERPMaterial.material_type,
                                               id=material_id)
        if not material:
            return
        dct["material_name"] = f"{material.name} ({material.material_type.name})"

    return dct


async def get_shift_product_bag_quantity(dialog_manager: DialogManager, **middleware_data):
    # Format("Текущая смена☞ дата: {shift_date} номер: {shift_number} время: {shift_duration} ч\n"
    #        "Продукция - {product_name}.\n"
    #        "👇Мешок: {bag_number} Количество: {product_quantity}.👇"),
    session = middleware_data.get('session')
    ctx = dialog_manager.current_context()
    shift_date = ctx.dialog_data.get("shift_date")
    shift_number = int(ctx.dialog_data.get("shift_number"))
    shift_duration = float(ctx.dialog_data.get("shift_duration"))
    product_id = int(n) if (n := ctx.dialog_data.get("product_id")) else 0
    product_line_number = int(n) if (n := ctx.dialog_data.get("product_line_number")) else 0
    dct = {"shift_date": shift_date,
           "shift_number": shift_number,
           "shift_duration": shift_duration,
           "bag_number": "#",
           "product_name": "",
           "product_quantity": 0}
    if product_line_number <= 0:
        product: ERPProduct = await dct_read(session, ERPProduct,
                                             joined_load=ERPProduct.product_type,
                                             id=product_id)
        if not product:
            return
        dct["product_name"] = f"{product.name} ({product.product_type.name})"

    return dct
