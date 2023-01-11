import datetime
import logging
from typing import List

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext, filters
from aiogram.types import Message, ChatActions, CallbackQuery
from aiogram.utils.markdown import text
from sqlalchemy.orm import sessionmaker

from tgbot.keyboards.shift_processing_inline import shift_kb, shift_menu_data, ShiftMenuAction, select_shift_kb, \
    multi_select_list_kb, ShiftMultiselect, shift_lookup_data, ShiftLookupAction, change_numeric_value_kb, \
    change_numeric_value, ChangeNumericValue, ShiftNavigator, ShiftEnterValue, select_edit_data_kb, select_edit_data, \
    SelectEditData
from tgbot.misc.datepicker_settings import get_datepicker_settings
from tgbot.models.erp_dict import dct_list, ERPEmployee, ERPActivity, dct_read, ERPMaterial, ERPProduct
from tgbot.models.erp_inventory import ERPMaterialIntake, material_intake_read_shift, material_intake_create, \
    shift_report_read_shift, ERPShiftReport, shift_report_create
from tgbot.models.erp_shift import shift_list_full, shift_create, shift_read, ERPShift, shift_navigator
from tgbot.widgets.aiogram_datepicker import Datepicker
from tgbot.widgets.aiogram_datepicker.callback_data import datepicker_callback
from tgbot.widgets.num_keypad.NumericKeypad import NumericKeypad

logger = logging.getLogger(__name__)


def get_staff(shift: ERPShift) -> str:
    return "\n".join([f"#{staff.employee.id} {staff.employee.name} ({staff.hours_worked})"
                      for staff in shift.shift_staff])


def get_activity(shift: ERPShift) -> str:
    return "\n".join([f"#{i} {activity.activity.name}" for i, activity in enumerate(shift.shift_activity, start=1)])


def get_selected_staff_text(staff_list: dict) -> str:
    return "\n".join(
        [text(f"#{item_id} {staff_list[item_id]['name']} ({staff_list[item_id]['hour']})"
              f"👉/edthour_{item_id}")
         for item_id in staff_list])


def get_selected_products(selected_products: dict) -> str:
    return "\n".join(
        [text(f"#{selected_products[item_id]['bag_number']} "
              f"{selected_products[item_id]['name']} "
              f"({selected_products[item_id]['weight']} кг)"
              f"👉/edtpr_{item_id}")
         for item_id in selected_products])


def get_shift_materials(materials: List[ERPMaterialIntake]) -> str:
    return "\n".join([f"#{material.line_number} "
                      f"{material.material.name} ({material.material.material_type.name})"
                      f" - {material.quantity} кг"
                      f" {'✅' if material.is_processed else '‼️'}"
                      for material in materials])


def get_shift_products(products: List[ERPShiftReport]) -> str:
    state = {'ok': '✅', 'todo': '‼️', 'back': '📛'}
    return "\n".join([f"#{product.id} "
                      f"{product.product.name} ({product.product.material_type.name})"
                      f" - {product.quantity} кг"
                      f" {state[product.report_state]}"
                      for product in products])


async def get_edit_product_text(product_id: str, state: FSMContext) -> str:
    async with state.proxy() as data:
        shift_date = datetime.date.fromisoformat(data["shift_date"])
        shift_number = int(data["shift_number"])
        data["product_id"] = product_id
        selected_products = data["selected_products"]
    product = selected_products[product_id]
    return (f"Дата смены:{shift_date.strftime('%d/%m/%Y')}\n"
            f"Номер смены: {shift_number}\n"
            f"Номер мешка: {product['bag_number']}\n"
            f"Продукция: {product['name']}\n"
            f"Вес: {product['weight']} кг")


async def get_shift_full_text(Session: sessionmaker,
                              shift_date: datetime.date,
                              shift_number: int) -> str:
    shift = await shift_read(Session=Session,
                             date=shift_date,
                             number=shift_number)
    shift_materials = await material_intake_read_shift(Session=Session,
                                                       shift_date=shift_date,
                                                       shift_number=shift_number)
    shift_products = await shift_report_read_shift(Session=Session,
                                                   shift_date=shift_date,
                                                   shift_number=shift_number)
    message_text = text(f"Дата смены:{shift.date.strftime('%d/%m/%Y')}\n"
                        f"Номер смены: {shift.number}\n"
                        f"Персонал:\n{get_staff(shift)}\n"
                        f"Работа:\n{get_activity(shift)}\n")
    if len(shift_materials):
        message_text += text(f"Сырье:\n{get_shift_materials(shift_materials)}\n")
    if len(shift_products):
        message_text += text(f"Продукция:\n{get_shift_products(shift_products)}")
    return message_text


async def shift_start(message: Message, state: FSMContext):
    await ChatActions.typing()
    Session = message.bot["Session"]
    shift_list = await shift_list_full(Session=Session, limit=1)
    last_shift_date = shift_list[0].date
    last_shift_number = shift_list[0].number
    if not len(shift_list):
        await message.answer("Необходимо создать смену", reply_markup=shift_kb(navigate=False))
        return
    async with state.proxy() as data:
        shift_date = last_shift_date if data.get("shift_date", None) is None else \
            datetime.date.fromisoformat(data["shift_date"])
        shift_number = last_shift_number if data.get("shift_number", None) is None else int(data["shift_number"])

        shift = await shift_read(Session=Session,
                                 date=shift_date,
                                 number=shift_number)
        if not shift:
            shift_list_next = await shift_navigator(Session, "next", date=shift_date, number=0, limit=1)
            shift_list_prev = await shift_navigator(Session, "prev", date=shift_date, number=4, limit=1)
            shift_list = shift_list_next if len(shift_list_next) else shift_list_prev
            shift_date = shift_list[0].date
            shift_number = shift_list[0].number
        data["shift_date"] = shift_date.isoformat()
        data["shift_number"] = shift_number
        data["selected_activity"] = []
        data["selected_staff"] = []

    message_text = await get_shift_full_text(Session, shift_date, shift_number)
    await message.answer(message_text, reply_markup=shift_kb(navigate=True))


async def shift_exit(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    await state.reset_state(with_data=False)
    await call.message.edit_reply_markup(reply_markup=None)


async def _process_shift_navigate(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    Session = call.message.bot["Session"]
    async with state.proxy() as data:
        shift_date = datetime.date.fromisoformat(data["shift_date"])
        shift_number = int(data["shift_number"])
    if callback_data['action'] == ShiftMenuAction.SM_SHIFT_PREV:
        shift_list = await shift_navigator(Session, "prev", date=shift_date, number=shift_number, limit=1)
    elif callback_data['action'] == ShiftMenuAction.SM_SHIFT_NEXT:
        shift_list = await shift_navigator(Session, "next", date=shift_date, number=shift_number, limit=1)
    else:
        async with state.proxy() as data:
            data["callback_data"] = callback_data
        current_state = await state.get_state()
        if current_state == "ShiftNavigator:shift_date_selected":
            await state.reset_state(with_data=False)
        else:
            await ShiftNavigator.shift_go_to.set()
            datepicker = Datepicker(get_datepicker_settings())
            markup = datepicker.start_calendar()
            await call.message.edit_text('Выберите дату: ', reply_markup=markup)
            return

        shift_list_next = await shift_navigator(Session, "next", date=shift_date, number=0, limit=1)
        shift_list_prev = await shift_navigator(Session, "prev", date=shift_date, number=4, limit=1)
        shift_list = shift_list_next if len(shift_list_next) else shift_list_prev

    if len(shift_list):
        shift_date = shift_list[0].date
        shift_number = shift_list[0].number
        async with state.proxy() as data:
            data["shift_date"] = shift_date.isoformat()
            data["shift_number"] = shift_number
        message_text = await get_shift_full_text(Session, shift_date, shift_number)
        await call.message.edit_text(message_text, reply_markup=shift_kb(navigate=True))


async def shift_new(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()

    datepicker = Datepicker(get_datepicker_settings())
    markup = datepicker.start_calendar()
    await call.message.edit_text('Выберите дату: ', reply_markup=markup)


async def _process_datepicker(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    datepicker = Datepicker(get_datepicker_settings())
    Session = call.message.bot["Session"]
    _date = await datepicker.process(call, callback_data)
    if _date:
        async with state.proxy() as data:
            data["shift_date"] = _date.isoformat()

        current_state = await state.get_state()
        if current_state == "ShiftNavigator:shift_go_to":
            await state.reset_state(with_data=False)
            async with state.proxy() as data:
                saved_callback_data = data["callback_data"]
            await ShiftNavigator.shift_date_selected.set()
            await _process_shift_navigate(call, saved_callback_data, state)
            return

        shifts = await shift_list_full(Session=Session, date=_date, limit=3)
        completed_shifts = [shift.number for shift in shifts]
        if len(completed_shifts) == 3:
            datepicker = Datepicker(get_datepicker_settings())
            markup = datepicker.start_calendar()
            await call.message.edit_text(text(f"На эту дату {_date.strftime('%d/%m/%Y')} "
                                              f"невозможно создать новую смену.\nВыберите другую дату: "),
                                         reply_markup=markup)
            return

        markup = select_shift_kb(completed_shifts)
        await call.message.edit_text(text(f"Дата смены:{_date.strftime('%d/%m/%Y')}\n"
                                          f"Выберите номер смены:"),
                                     reply_markup=markup)


async def _process_select_shift(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    Session = call.message.bot["Session"]
    shift_number = -1
    if callback_data["action"] == ShiftMenuAction.SM_CANCEL:
        await state.reset_state(with_data=False)
        await call.message.delete()
        return
    elif callback_data["action"] == ShiftMenuAction.SM_IGNORE:
        return
    elif callback_data["action"] == ShiftMenuAction.SM_SHIFT_SELECT:
        shift_number = int(callback_data["shift_number"])
        async with state.proxy() as data:
            shift_date = datetime.date.fromisoformat(data["shift_date"])
            data["shift_number"] = shift_number
            data["selected_staff"] = {}
    staff_list = await dct_list(Session=Session, table_class=ERPEmployee, is_active=True)
    markup = multi_select_list_kb(staff_list, [], row_width=2)
    await call.message.edit_text((f"Дата смены:{shift_date.strftime('%d/%m/%Y')}\n"
                                  f"Номер смены: {shift_number}\n"
                                  f"Выберите персонал:"),
                                 reply_markup=markup)
    await ShiftMultiselect.select_staff.set()


async def _process_shift_staff(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    Session = call.message.bot["Session"]
    async with state.proxy() as data:
        shift_date = datetime.date.fromisoformat(data["shift_date"])
        shift_number = int(data["shift_number"])
        data["message_id"] = call.message.message_id
        data["chat_id"] = call.message.chat.id
        data["callback_data"] = callback_data
    if callback_data["action"] == ShiftLookupAction.SL_LOOKUP_CANCEL:
        await state.reset_state(with_data=False)
        await call.message.delete()
        return
    elif callback_data["action"] == ShiftLookupAction.SL_LOOKUP_SELECT:
        async with state.proxy() as data:
            selected_staff = data["selected_staff"]
        if int(callback_data["item_id"]) > 0:
            if callback_data["item_id"] in selected_staff.keys():
                selected_staff.pop(callback_data["item_id"])
            else:
                employee = await dct_read(Session, ERPEmployee, id=int(callback_data["item_id"]))
                selected_staff[callback_data["item_id"]] = {"name": employee.name, "hour": 8}
        async with state.proxy() as data:
            data["selected_staff"] = selected_staff
        staff_list = await dct_list(Session=Session, table_class=ERPEmployee, is_active=True)
        markup = multi_select_list_kb(staff_list, list(map(int, selected_staff.keys())), row_width=2)
        selected_staff_text = get_selected_staff_text(selected_staff)
        await call.message.edit_text((f"Дата смены:{shift_date.strftime('%d/%m/%Y')}\n"
                                      f"Номер смены: {shift_number}\n"
                                      f"Персонал:\n{selected_staff_text}"),
                                     reply_markup=markup)
    elif callback_data["action"] == ShiftLookupAction.SL_LOOKUP_CONFIRM:
        async with state.proxy() as data:
            selected_staff_text = get_selected_staff_text(data["selected_staff"])
            data["selected_activity"] = []
            activity_list = await dct_list(Session=Session, table_class=ERPActivity, is_active=True)
            markup = multi_select_list_kb(activity_list, [], row_width=2)
            await call.message.edit_text((f"Дата смены:{shift_date.strftime('%d/%m/%Y')}\n"
                                          f"Номер смены: {shift_number}\n"
                                          f"Персонал: \n{selected_staff_text}\n"
                                          f"Выберите работы:"),
                                         reply_markup=markup)
        await ShiftMultiselect.select_activity.set()


async def _edit_hour(message: Message, regexp_command, state: FSMContext):
    await ChatActions.typing()
    employee_id = int(regexp_command.group(1))
    async with state.proxy() as data:
        shift_date = datetime.date.fromisoformat(data["shift_date"])
        shift_number = int(data["shift_number"])
        data["employee_id"] = employee_id
        staff_list = data["selected_staff"]
        message_id = int(data["message_id"])
        chat_id = int(data["chat_id"])
    await message.delete()
    employee = staff_list[str(employee_id)]
    markup = change_numeric_value_kb()
    await message.bot.edit_message_text((f"Дата смены:{shift_date.strftime('%d/%m/%Y')}\n"
                                         f"Номер смены: {shift_number}\n"
                                         f"Персонал: {employee['name']}\n"
                                         f"Часы:{employee['hour']}"),
                                        chat_id=chat_id,
                                        message_id=message_id,
                                        reply_markup=markup)


async def _process_edit_hour(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    async with state.proxy() as data:
        shift_date = datetime.date.fromisoformat(data["shift_date"])
        shift_number = int(data["shift_number"])
        employee_id = data["employee_id"]
        staff_list = data["selected_staff"]
        saved_callback_data = data["callback_data"]
    saved_callback_data["item_id"] = -int(employee_id)
    employee = staff_list[str(employee_id)]
    wh = int(employee["hour"])
    markup = change_numeric_value_kb()
    if callback_data["action"] == ChangeNumericValue.CNV_INC:
        wh = 4 if wh == 8 else (wh + 4)
    elif callback_data["action"] == ChangeNumericValue.CNV_DEC:
        wh = 8 if wh == 4 else (wh - 4)
    elif callback_data["action"] == ChangeNumericValue.CNV_CONFIRM:
        staff_list[str(employee_id)]["hour"] = wh
        async with state.proxy() as data:
            data["selected_staff"] = staff_list
        await _process_shift_staff(call, saved_callback_data, state)
        return
    elif callback_data["action"] == ChangeNumericValue.CNV_CANCEL:
        await _process_shift_staff(call, saved_callback_data, state)
        return
    staff_list[str(employee_id)]["hour"] = wh
    async with state.proxy() as data:
        data["selected_staff"] = staff_list
    await call.message.edit_text((f"Дата смены:{shift_date.strftime('%d/%m/%Y')}\n"
                                  f"Номер смены: {shift_number}\n"
                                  f"Персонал: {employee['name']}\n"
                                  f"Часы: {wh}"),
                                 reply_markup=markup)


async def _process_shift_activity(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    Session = call.message.bot["Session"]
    if callback_data["action"] == ShiftLookupAction.SL_LOOKUP_CANCEL:
        await state.reset_state(with_data=False)
        await call.message.delete()
        return
    elif callback_data["action"] == ShiftLookupAction.SL_LOOKUP_SELECT:
        async with state.proxy() as data:
            shift_date = datetime.date.fromisoformat(data["shift_date"])
            shift_number = int(data["shift_number"])
            selected_activity: list = data["selected_activity"]
            selected_staff_text = get_selected_staff_text(data["selected_staff"])

        if callback_data["item_id"] in selected_activity:
            selected_activity.remove(callback_data["item_id"])
        else:
            selected_activity.append(callback_data["item_id"])
        async with state.proxy() as data:
            data["selected_activity"] = selected_activity
        activity_list = await dct_list(Session=Session, table_class=ERPActivity, is_active=True)
        markup = multi_select_list_kb(activity_list, list(map(int, selected_activity)), row_width=2)
        await call.message.edit_text((f"Дата смены:{shift_date.strftime('%d/%m/%Y')}\n"
                                      f"Номер смены: {shift_number}\n"
                                      f"Персонал:\n{selected_staff_text}"),
                                     reply_markup=markup)
    elif callback_data["action"] == ShiftLookupAction.SL_LOOKUP_CONFIRM:
        async with state.proxy() as data:
            shift_date = datetime.date.fromisoformat(data["shift_date"])
            shift_number = int(data["shift_number"])
            selected_activity: list = list(map(int, data["selected_activity"]))
            staff_list = data["selected_staff"]
        await state.reset_state(with_data=False)
        shift = await shift_create(Session=Session, date=shift_date, number=shift_number,
                                   staff_list=staff_list, activity_list=selected_activity)
        async with state.proxy() as data:
            data["selected_activity"] = []
            data["selected_staff"] = []
        await call.message.edit_text((f"Дата смены:{shift.date.strftime('%d/%m/%Y')}\n"
                                      f"Номер смены: {shift_number}\n"
                                      f"Персонал:\n{get_staff(shift)}\n"
                                      f"Работа:\n{get_activity(shift)}"))


async def _prepare_shift_materials(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    Session = call.message.bot["Session"]

    async with state.proxy() as data:
        shift_date = datetime.date.fromisoformat(data["shift_date"])
        shift_number = data["shift_number"]
        data["selected_materials"] = {}
    message_text = text(f"Дата смены:{shift_date.strftime('%d/%m/%Y')}\n"
                        f"Номер смены: {shift_number}\n"
                        f"Выберите сырье:")
    materials = await dct_list(Session, ERPMaterial, is_active=True)

    shift_materials = await material_intake_read_shift(Session=Session,
                                                       shift_date=shift_date,
                                                       shift_number=shift_number,
                                                       desc=True,
                                                       limit=1)
    start_line = shift_materials[0].line_number + 1 if len(shift_materials) else 1
    async with state.proxy() as data:
        data["start_line"] = start_line

    markup = multi_select_list_kb(materials, [], row_width=2)
    await call.message.edit_text(message_text, reply_markup=markup)
    await ShiftMultiselect.select_materials.set()


async def _process_shift_materials(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    Session = call.message.bot["Session"]
    async with state.proxy() as data:
        shift_date = datetime.date.fromisoformat(data["shift_date"])
        shift_number = data["shift_number"]
        selected_materials = data["selected_materials"]
    if callback_data["action"] == ShiftLookupAction.SL_LOOKUP_CANCEL:
        await state.reset_state(with_data=False)
        message_text = await get_shift_full_text(Session, shift_date, shift_number)
        markup = shift_kb(navigate=True)
        await call.message.edit_text(message_text, reply_markup=markup)
        return
    elif callback_data["action"] == ShiftLookupAction.SL_LOOKUP_SELECT:

        if callback_data["item_id"] in selected_materials.keys():
            selected_materials.pop(callback_data["item_id"])
        elif int(callback_data["item_id"]) >= 0:
            material = await dct_read(Session, ERPMaterial, id=int(callback_data["item_id"]))
            selected_materials[callback_data["item_id"]] = {"name": material.name, "weight": 0}
        async with state.proxy() as data:
            data["callback_data"] = callback_data
            data["selected_materials"] = selected_materials
            data["message_id"] = call.message.message_id
            data["chat_id"] = call.message.chat.id
        selected_materials_text = "\n".join(
            [text(f"#{item_id} {selected_materials[item_id]['name']} ({selected_materials[item_id]['weight']} кг)"
                  f"👉/edtmw_{item_id}")
             for item_id in selected_materials])
        materials = await dct_list(Session, ERPMaterial, joined_load=ERPMaterial.material_type, is_active=True)
        markup = multi_select_list_kb(materials, list(map(int, selected_materials.keys())), row_width=2)
        message_text = text(f"Дата смены:{shift_date.strftime('%d/%m/%Y')}\n"
                            f"Номер смены: {shift_number}\n"
                            f"Сырье:\n{selected_materials_text}")
        await call.message.edit_text(message_text, reply_markup=markup)
    elif callback_data["action"] == ShiftLookupAction.SL_LOOKUP_CONFIRM:
        await state.reset_state(with_data=False)
        async with state.proxy() as data:
            start_line = int(data["start_line"])
        await material_intake_create(Session,
                                     shift_date=shift_date,
                                     shift_number=shift_number,
                                     materials=selected_materials,
                                     start_line=start_line)

        message_text = await get_shift_full_text(Session, shift_date, shift_number)
        markup = shift_kb(navigate=True)
        await call.message.edit_text(message_text, reply_markup=markup)


async def _edit_material_weight(message: Message, regexp_command, state: FSMContext):
    await ChatActions.typing()
    material_id = int(regexp_command.group(1))
    async with state.proxy() as data:
        shift_date = datetime.date.fromisoformat(data["shift_date"])
        shift_number = int(data["shift_number"])
        data["material_id"] = material_id
        selected_materials = data["selected_materials"]
        message_id = int(data["message_id"])
        chat_id = int(data["chat_id"])
    await message.delete()
    material = selected_materials[str(material_id)]
    num_keypad = NumericKeypad(material['weight'])
    message_text = (f"Дата смены:{shift_date.strftime('%d/%m/%Y')}\n"
                    f"Номер смены: {shift_number}\n"
                    f"Сырье: {material['name']}\n"
                    f"Вес: {material['weight']} кг")
    markup = num_keypad.start()
    await message.bot.edit_message_text(message_text,
                                        chat_id=chat_id,
                                        message_id=message_id,
                                        reply_markup=markup)
    await ShiftEnterValue.material_weight.set()


async def _process_material_weight(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    async with state.proxy() as data:
        shift_date = datetime.date.fromisoformat(data["shift_date"])
        shift_number = int(data["shift_number"])
        material_id = data["material_id"]
        selected_materials = data["selected_materials"]
        saved_callback_data = data["callback_data"]
    material = selected_materials[str(material_id)]
    num_keypad = NumericKeypad(material['weight'])
    message_text = (f"Дата смены:{shift_date.strftime('%d/%m/%Y')}\n"
                    f"Номер смены: {shift_number}\n"
                    f"Сырье: {material['name']}\n"
                    f"Вес: /*value*/ кг")
    num_keypad.message_text = message_text
    value = await num_keypad.process(call, callback_data)
    if value is not None:
        await ShiftMultiselect.select_materials.set()
        selected_materials[str(material_id)]['weight'] = value
        async with state.proxy() as data:
            data["selected_materials"] = selected_materials
        saved_callback_data["item_id"] = -1
        await _process_shift_materials(call, saved_callback_data, state)


async def _prepare_shift_products(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    Session = call.message.bot["Session"]

    async with state.proxy() as data:
        shift_date = datetime.date.fromisoformat(data["shift_date"])
        shift_number = data["shift_number"]
        data["selected_products"] = {}
    message_text = text(f"Дата смены:{shift_date.strftime('%d/%m/%Y')}\n"
                        f"Номер смены: {shift_number}\n"
                        f"Выберите продукцию:")
    products = await dct_list(Session, ERPProduct, is_active=True)

    markup = multi_select_list_kb(products, [], row_width=2)
    await call.message.edit_text(message_text, reply_markup=markup)
    await ShiftMultiselect.select_products.set()


async def _process_shift_products(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    Session = call.message.bot["Session"]
    async with state.proxy() as data:
        shift_date = datetime.date.fromisoformat(data["shift_date"])
        shift_number = data["shift_number"]
        selected_products = data["selected_products"]
    if callback_data["action"] == ShiftLookupAction.SL_LOOKUP_CANCEL:
        await state.reset_state(with_data=False)
        message_text = await get_shift_full_text(Session, shift_date, shift_number)
        markup = shift_kb(navigate=True)
        await call.message.edit_text(message_text, reply_markup=markup)
        return
    elif callback_data["action"] == ShiftLookupAction.SL_LOOKUP_SELECT:

        if callback_data["item_id"] in selected_products.keys():
            selected_products.pop(callback_data["item_id"])
        elif int(callback_data["item_id"]) >= 0:
            product = await dct_read(Session, ERPProduct, id=int(callback_data["item_id"]))
            selected_products[callback_data["item_id"]] = {"name": product.name,
                                                           "weight": 0,
                                                           "bag_number": 0}
        async with state.proxy() as data:
            data["callback_data"] = callback_data
            data["selected_products"] = selected_products
            data["message_id"] = call.message.message_id
            data["chat_id"] = call.message.chat.id
        selected_products_text = get_selected_products(selected_products)
        products = await dct_list(Session, ERPProduct, joined_load=ERPProduct.material_type, is_active=True)
        markup = multi_select_list_kb(products, list(map(int, selected_products.keys())), row_width=2)
        message_text = text(f"Дата смены:{shift_date.strftime('%d/%m/%Y')}\n"
                            f"Номер смены: {shift_number}\n"
                            f"Продукция:\n{selected_products_text}")
        await call.message.edit_text(message_text, reply_markup=markup)
    elif callback_data["action"] == ShiftLookupAction.SL_LOOKUP_CONFIRM:
        await state.reset_state(with_data=False)
        await shift_report_create(Session,
                                  shift_date=shift_date,
                                  shift_number=shift_number,
                                  products=selected_products)
        message_text = await get_shift_full_text(Session, shift_date, shift_number)
        markup = shift_kb(navigate=True)
        await call.message.edit_text(message_text, reply_markup=markup)


async def _prepare_edit_product(message: Message, regexp_command, state: FSMContext):
    await ChatActions.typing()
    product_id = regexp_command.group(1)
    async with state.proxy() as data:
        data["product_id"] = product_id
        message_id = int(data["message_id"])
        chat_id = int(data["chat_id"])
    message_text = await get_edit_product_text(product_id, state)
    await message.delete()
    markup = select_edit_data_kb()
    await message.bot.edit_message_text(message_text,
                                        chat_id=chat_id,
                                        message_id=message_id,
                                        reply_markup=markup)


async def _process_edit_product(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    Session = call.message.bot["Session"]
    async with state.proxy() as data:
        shift_date = datetime.date.fromisoformat(data["shift_date"])
        shift_number = data["shift_number"]
        selected_products = data["selected_products"]
        product_id = data["product_id"]
        data['callback_data'] = callback_data
    if callback_data["key_value"] == SelectEditData.SED_BACK:
        selected_products_text = get_selected_products(selected_products)
        products = await dct_list(Session, ERPProduct, joined_load=ERPProduct.material_type, is_active=True)
        markup = multi_select_list_kb(products, list(map(int, selected_products.keys())), row_width=2)
        message_text = text(f"Дата смены:{shift_date.strftime('%d/%m/%Y')}\n"
                            f"Номер смены: {shift_number}\n"
                            f"Продукция:\n{selected_products_text}")
        await call.message.edit_text(message_text, reply_markup=markup)
        return
    elif callback_data["key_value"] == SelectEditData.SED_BAG_NUMBER:
        product = selected_products[str(product_id)]
        message_text = await get_edit_product_text(product_id, state)
        num_keypad = NumericKeypad(product['bag_number'])
        markup = num_keypad.start()
        await call.message.edit_text(message_text, reply_markup=markup)
        await ShiftEnterValue.product_bag.set()
    elif callback_data["key_value"] == SelectEditData.SED_WEIGHT:
        product = selected_products[str(product_id)]
        message_text = await get_edit_product_text(product_id, state)
        num_keypad = NumericKeypad(product['weight'])
        markup = num_keypad.start()
        await call.message.edit_text(message_text, reply_markup=markup)
        await ShiftEnterValue.product_weight.set()


async def _process_enter_product_bag(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    async with state.proxy() as data:
        shift_date = datetime.date.fromisoformat(data["shift_date"])
        shift_number = data["shift_number"]
        selected_products = data["selected_products"]
        product_id = data["product_id"]
    product = selected_products[str(product_id)]
    num_keypad = NumericKeypad(product['bag_number'])
    message_text = ((f"Дата смены:{shift_date.strftime('%d/%m/%Y')}\n"
                     f"Номер смены: {shift_number}\n"
                     f"Номер мешка: /*value*/\n"
                     f"Продукция: {product['name']}\n"
                     f"Вес: {product['weight']} кг"))
    num_keypad.message_text = message_text
    value = await num_keypad.process(call, callback_data)
    if value is not None:
        selected_products[str(product_id)]['bag_number'] = value
        async with state.proxy() as data:
            data["selected_products"] = selected_products
        await state.reset_state(with_data=False)
        async with state.proxy() as data:
            data["product_id"] = product_id
        message_text = await get_edit_product_text(product_id, state)
        markup = select_edit_data_kb()
        await call.message.edit_text(message_text, reply_markup=markup)
        await ShiftMultiselect.select_products.set()


async def _process_enter_product_weight(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    async with state.proxy() as data:
        shift_date = datetime.date.fromisoformat(data["shift_date"])
        shift_number = data["shift_number"]
        selected_products = data["selected_products"]
        product_id = data["product_id"]
    product = selected_products[str(product_id)]
    num_keypad = NumericKeypad(product['weight'])
    message_text = ((f"Дата смены:{shift_date.strftime('%d/%m/%Y')}\n"
                     f"Номер смены: {shift_number}\n"
                     f"Номер мешка: {product['bag_number']}\n"
                     f"Продукция: {product['name']}\n"
                     f"Вес: /*value*/ кг"))
    num_keypad.message_text = message_text
    value = await num_keypad.process(call, callback_data)
    if value is not None:
        selected_products[str(product_id)]['weight'] = value
        async with state.proxy() as data:
            data["selected_products"] = selected_products
        await state.reset_state(with_data=False)
        async with state.proxy() as data:
            data["product_id"] = product_id
        message_text = await get_edit_product_text(product_id, state)
        markup = select_edit_data_kb()
        await call.message.edit_text(message_text, reply_markup=markup)
        await ShiftMultiselect.select_products.set()


def register_shift(dp: Dispatcher):
    dp.register_message_handler(shift_start, commands=["shift"], state="*")
    dp.register_message_handler(_edit_hour,
                                filters.RegexpCommandsFilter(regexp_commands=['edthour_([0-9]*)']), state="*")
    dp.register_message_handler(_edit_material_weight,
                                filters.RegexpCommandsFilter(regexp_commands=['edtmw_([0-9]*)']), state="*")
    dp.register_message_handler(_prepare_edit_product,
                                filters.RegexpCommandsFilter(regexp_commands=['edtpr_([0-9]*)']), state="*")
    dp.register_callback_query_handler(shift_exit,
                                       shift_menu_data.filter(action=ShiftMenuAction.SM_SHIFT_EXIT),
                                       state="*")
    dp.register_callback_query_handler(shift_new,
                                       shift_menu_data.filter(action=ShiftMenuAction.SM_SHIFT_NEW),
                                       state="*")
    dp.register_callback_query_handler(_process_datepicker,
                                       datepicker_callback.filter(),
                                       state="*")
    dp.register_callback_query_handler(_process_select_shift,
                                       shift_menu_data.filter(action=[ShiftMenuAction.SM_IGNORE,
                                                                      ShiftMenuAction.SM_SHIFT_SELECT,
                                                                      ShiftMenuAction.SM_CANCEL]),
                                       state="*")
    dp.register_callback_query_handler(_process_shift_staff,
                                       shift_lookup_data.filter(action=[ShiftLookupAction.SL_LOOKUP_SELECT,
                                                                        ShiftLookupAction.SL_LOOKUP_CONFIRM,
                                                                        ShiftLookupAction.SL_LOOKUP_CANCEL]),
                                       state=ShiftMultiselect.select_staff)
    dp.register_callback_query_handler(_process_shift_activity,
                                       shift_lookup_data.filter(action=[ShiftLookupAction.SL_LOOKUP_SELECT,
                                                                        ShiftLookupAction.SL_LOOKUP_CONFIRM,
                                                                        ShiftLookupAction.SL_LOOKUP_CANCEL]),
                                       state=ShiftMultiselect.select_activity)
    dp.register_callback_query_handler(_process_shift_navigate,
                                       shift_menu_data.filter(action=[ShiftMenuAction.SM_SHIFT_PREV,
                                                                      ShiftMenuAction.SM_SHIFT_NEXT,
                                                                      ShiftMenuAction.SM_SHIFT_GOTO]),
                                       state="*")
    dp.register_callback_query_handler(_process_edit_hour,
                                       change_numeric_value.filter(),
                                       state="*")
    dp.register_callback_query_handler(_prepare_shift_materials,
                                       shift_menu_data.filter(action=ShiftMenuAction.SM_SHIFT_MATERIAL),
                                       state="*")
    dp.register_callback_query_handler(_prepare_shift_products,
                                       shift_menu_data.filter(action=ShiftMenuAction.SM_SHIFT_PRODUCT),
                                       state="*")
    dp.register_callback_query_handler(_process_shift_materials,
                                       shift_lookup_data.filter(action=[ShiftLookupAction.SL_LOOKUP_SELECT,
                                                                        ShiftLookupAction.SL_LOOKUP_CONFIRM,
                                                                        ShiftLookupAction.SL_LOOKUP_CANCEL]),
                                       state=ShiftMultiselect.select_materials)
    dp.register_callback_query_handler(_process_shift_products,
                                       shift_lookup_data.filter(action=[ShiftLookupAction.SL_LOOKUP_SELECT,
                                                                        ShiftLookupAction.SL_LOOKUP_CONFIRM,
                                                                        ShiftLookupAction.SL_LOOKUP_CANCEL]),
                                       state=ShiftMultiselect.select_products)
    dp.register_callback_query_handler(_process_material_weight,
                                       NumericKeypad.callback.filter(),
                                       state=ShiftEnterValue.material_weight)
    dp.register_callback_query_handler(_process_edit_product,
                                       select_edit_data.filter(),
                                       state="*")
    dp.register_callback_query_handler(_process_enter_product_bag,
                                       NumericKeypad.callback.filter(),
                                       state=ShiftEnterValue.product_bag)
    dp.register_callback_query_handler(_process_enter_product_weight,
                                       NumericKeypad.callback.filter(),
                                       state=ShiftEnterValue.product_weight)
