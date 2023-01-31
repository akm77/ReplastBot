import datetime
from typing import Optional, List

from . import constants
from .constants import ShiftDialogId
from ...models.erp_dict import ERPEmployee, dct_list
from ...models.erp_shift_staff_activity import shift_list_full, shift_read, ERPShift
from ...widgets.aiogram_dialog import DialogManager
from ...widgets.aiogram_dialog.widgets.kbd import Multiselect


def get_shift_staff_list(shift: ERPShift) -> Optional[List]:
    staff_button = [("<- ПЕРСОНАЛ ->", -1)]
    return staff_button + [(f"{employee.employee.name} - {employee.hours_worked} ч", employee.employee_id)
                           for employee in shift.shift_staff]


def get_shift_activity_list(shift: ERPShift) -> Optional[List]:
    activity_button = [("<- РАБОТЫ ->", -1)]
    return activity_button + [(f"{activity.activity.name}", activity.activity_id)
                              for activity in shift.shift_activity]


def get_shift_material_list(shift: ERPShift) -> Optional[List]:
    material_button = [("<- СЫРЬЁ ->", "-1_-1")]
    return material_button + [(f"#{material.line_number} {material.material.name} - "
                               f"{material.quantity} {material.material.uom_code} "
                               f"{'✅' if material.is_processed else '‼️'}",
                               f"{material.line_number}_{material.material_id}")
                              for material in shift.shift_material_intake]


def get_shift_product_list(shift: ERPShift) -> Optional[List]:
    state = {'ok': '✅', 'todo': '‼️', 'back': '📛'}
    product_button = [("<- ПРОДУКЦИЯ ->", "-1_-1")]
    return product_button + [(f"#{product.id} {product.product.name} - "
                              f"{product.quantity} {product.product.uom_code} "
                              f"{state[product.report_state]}",
                              f"{product.id}_{product.product_id}")
                             for product in shift.shift_production]


async def get_shift_list(dialog_manager: DialogManager, **middleware_data):
    session = middleware_data.get('session')
    ctx = dialog_manager.current_context()

    db_shift_list = await shift_list_full(session, reverse=False)
    shift_list = [
        (f'{shift.date: %d.%m.%Y} смена: {shift.number} ({shift.duration} ч)', f'{shift.date}_{shift.number}')
        for shift in db_shift_list
    ]
    page = int(page) if (page := ctx.widget_data.get(constants.ShiftDialogId.SHIFT_LIST)) else 0
    shift_date, shift_number = shift_list[page][1].split("_")
    ctx.dialog_data.update(shift_date=shift_date, shift_number=shift_number)
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
    shift_staff = [employee.employee_id for employee in shift.shift_staff]
    ctx.widget_data.update(start_shift_staff=shift_staff)
    employee = [(employee.name, employee.id) for employee in db_employee_list]
    _ = [(await employee_ms.set_checked(event=dialog_manager.event,
                                        item_id=str(e[1]),
                                        checked=True,
                                        manager=dialog_manager)) for e in employee if e[1] in shift_staff]
    return {"employee": employee}
