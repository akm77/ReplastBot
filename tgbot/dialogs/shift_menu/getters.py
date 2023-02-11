import datetime
from typing import Optional, List

from . import constants
from .constants import ShiftDialogId
from ...models.erp_dict import ERPEmployee, dct_list
from ...models.erp_shift import ERPShift, shift_list_full, shift_read, get_shift_staff_member, select_day_shift_numbers
from ...widgets.aiogram_dialog import DialogManager
from ...widgets.aiogram_dialog.widgets.kbd import Multiselect, Radio


def get_shift_staff_list(shift: ERPShift) -> Optional[List]:
    staff_button = [("<- ПЕРСОНАЛ ->", -1)]
    return staff_button + [(f"{employee.employee.name} - {employee.hours_worked} ч", employee.employee_id)
                           for employee in shift.shift_staff]


def get_shift_activity_list(shift: ERPShift) -> Optional[List]:
    activity_button = [("<- РАБОТЫ ->", -1)]
    return activity_button + [(f"{activity.activity.name}", activity.activity_id)
                              for activity in shift.shift_activities]


def get_shift_material_list(shift: ERPShift) -> Optional[List]:
    material_button = [("<- СЫРЬЁ ->", "-1_-1")]
    return material_button + [(f"#{material.line_number} {material.material.name} - "
                               f"{material.quantity} {material.material.uom_code} "
                               f"{'✅' if material.is_processed else '‼️'}",
                               f"{material.line_number}_{material.material_id}")
                              for material in shift.shift_materials]


def get_shift_product_list(shift: ERPShift) -> Optional[List]:
    state = {'ok': '✅', 'todo': '‼️', 'back': '📛'}
    product_button = [("<- ПРОДУКЦИЯ ->", "-1_-1")]
    return product_button + [(f"#{product.id} {product.product.name} - "
                              f"{product.quantity} {product.product.uom_code} "
                              f"{state[product.state]}",
                              f"{product.id}_{product.product_id}")
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
    db_day_shift_numbers = await select_day_shift_numbers(session,
                                                          date=datetime.date.fromisoformat(shift_date))
    day_shift_numbers = [shift.number for shift in db_day_shift_numbers]
    ctx.dialog_data.update(day_shift_numbers=day_shift_numbers)
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
    day_shift_numbers = ctx.dialog_data.get("day_shift_numbers")
    shift_numbers = [(int(shift_number), int(shift_number)) for shift_number in day_shift_numbers]
    radio: Radio = dialog_manager.dialog().find(constants.ShiftDialogId.SHIFT_NUMBER_SELECT)
    # d = radio.get_checked(dialog_manager)
    # if not radio.get_checked(dialog_manager):
    #     await radio.set_checked(event=dialog_manager.event,
    #                             item_id=shift_number,
    #                             manager=dialog_manager)
    return {"shift_date": shift_date,
            "shift_number": shift_number,
            "shift_duration": shift_duration,
            "shift_numbers": shift_numbers}


async def get_employee_list(dialog_manager: DialogManager, **middleware_data):
    ctx = dialog_manager.current_context()
    shift_date = ctx.dialog_data.get("shift_date")
    shift_number = ctx.dialog_data.get("shift_number")
    employee_ms: Multiselect = dialog_manager.dialog().find(ShiftDialogId.SELECT_SHIFT_STAFF)
    session = middleware_data.get('session')
    db_employee_list = await dct_list(Session=session, table_class=ERPEmployee)
    shift = await shift_read(session,
                             date=datetime.date.fromisoformat(shift_date),
                             number=int(shift_number))
    start_shift_staff = [str(employee.employee_id) for employee in shift.shift_staff]
    current_shift_staff = c if (c := ctx.widget_data.get("current_shift_staff")) is not None else start_shift_staff
    ctx.widget_data.update(start_shift_staff=start_shift_staff)
    ctx.widget_data.update(current_shift_staff=current_shift_staff)
    employee = [(employee.name, employee.id) for employee in db_employee_list]
    _ = [(await employee_ms.set_checked(event=dialog_manager.event,
                                        item_id=str(e[1]),
                                        checked=True,
                                        manager=dialog_manager)) for e in employee
         if str(e[1]) in current_shift_staff]
    return {"employee": employee}


async def get_staff_employee(dialog_manager: DialogManager, **middleware_data):
    session = middleware_data.get('session')
    ctx = dialog_manager.current_context()
    shift_date = ctx.dialog_data.get("shift_date")
    shift_number = ctx.dialog_data.get("shift_number")
    employee_id = ctx.dialog_data.get("employee_id")
    employee = await get_shift_staff_member(Session=session,
                                            shift_date=datetime.date.fromisoformat(shift_date),
                                            shift_number=int(shift_number),
                                            employee_id=int(employee_id))
    employee_name = employee.employee.name
    employee_shift_date = employee.shift_date.strftime("%d.%m.%Y")
    employee_shift_number = employee.shift_number
    employee_hours_worked = employee.hours_worked
    return {"employee_name": employee_name,
            "employee_shift_date": employee_shift_date,
            "employee_shift_number": employee_shift_number,
            "employee_hours_worked": employee_hours_worked}
