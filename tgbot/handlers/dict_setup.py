import logging
from pprint import pprint
from typing import Union

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ChatActions, CallbackQuery, ForceReply
from aiogram.utils.markdown import text
from sqlalchemy.orm import sessionmaker

from tgbot.keyboards.dict_setup_inline import main_menu_kb, main_menu_data, MainMenuAction, dict_list_kb, \
    SimpleDictMenuAction, dict_menu_data, DctEdit, dict_edit_kb, confirm_kb, lookup_kb
from tgbot.models.erp_dict import dct_list, dct_create, dct_update, dct_read, dct_delete, DICT_LIST, DictType, \
    ERPMaterial, ERPContractor, ERPMaterialType, ERPCity, ERPEmployee, ERPProduct, ERPProductType

logger = logging.getLogger(__name__)


async def get_dict_text(Session: sessionmaker,
                        dict_class: Union[ERPEmployee, ERPCity, ERPMaterialType,
                                          ERPProduct, ERPMaterial, ERPContractor],
                        line_id: int) -> tuple[Union[ERPEmployee, ERPCity, ERPMaterialType,
                                                     ERPProduct, ERPMaterial, ERPContractor], str]:
    custom_text = ""
    if dict_class.__name__ == "ERPMaterial":
        dict_obj = await dct_read(Session, dict_class, id=line_id, joined_load=ERPMaterial.material_type)
        custom_text = text(f"Тип: {dict_obj.material_type.name}\n"
                           f"Примеси: {dict_obj.impurity}%\n")
    elif dict_class.__name__ == "ERPProduct":
        dict_obj = await dct_read(Session, dict_class, id=line_id, joined_load=ERPProduct.product_type)
        custom_text = f"Тип: {dict_obj.product_type.name}\n"
    elif dict_class.__name__ == "ERPContractor":
        dict_obj = await dct_read(Session, dict_class, id=line_id, joined_load=ERPContractor.city)
        # city = relationship("ERPCity", backref=backref("erp_contractor", uselist=False))
        # is_provider = Column(Boolean, nullable=False, server_default=expression.true())
        # is_buyer = Column(Boolean, nullable=False, server_default=expression.false())

        custom_text = text(f"Город: {dict_obj.city.name}\n"
                           f"Поставщик: {'✅' if dict_obj.is_provider else '⬛️️'}\n"
                           f"Покупатель: {'✅' if dict_obj.is_buyer else '⬛'}\n")
    else:
        dict_obj = await dct_read(Session, dict_class, id=line_id)

    message_text = text(f"ID: {dict_obj.id}\n"
                        f"{dict_obj.hr_names['name_name']}: {dict_obj.name}\n"
                        f"Активен: {'🔔' if dict_obj.is_active else '🔕'}\n") + custom_text
    return dict_obj, message_text


async def main_menu(message: Message, state: FSMContext):
    await ChatActions.typing()
    async with state.proxy() as data:
        data["user_mention"] = message.from_user.mention
        data["dict_id"] = -1
        data["line_id"] = -1
    await message.answer(text(f"Привет {message.from_user.mention}!\n"
                              f"Выбери справочник для работы"),
                         disable_web_page_preview=True,
                         reply_markup=main_menu_kb())


async def main_menu_exit(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    try:
        await call.message.delete()
        await state.finish()
    except Exception as err:
        logger.error("Error while deleting message. %r", err)


async def back_to_main_menu(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    try:
        async with state.proxy() as data:
            user_mention = data["user_mention"]
        await call.message.edit_text(text(f"Привет {user_mention}!\n"
                                          f"Выбери справочник для работы"),
                                     disable_web_page_preview=True,
                                     reply_markup=main_menu_kb())
    except Exception as err:
        logger.error("Error while editing message. %r", err)


async def dict_list_view(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    Session = call.message.bot["Session"]
    async with state.proxy() as data:
        data["dict_id"] = dict_id = callback_data.get("dict_id") or data["dict_id"]
    dict_class = DICT_LIST[int(dict_id)]
    if dict_class.__name__ == "ERPMaterial":
        dict_list = await dct_list(Session, dict_class, joined_load=ERPMaterial.material_type)
    elif dict_class.__name__ == "ERPProduct":
        dict_list = await dct_list(Session, dict_class, joined_load=ERPProduct.product_type)
    elif dict_class.__name__ == "ERPContractor":
        dict_list = await dct_list(Session, dict_class, joined_load=ERPContractor.city)
    else:
        dict_list = await dct_list(Session, dict_class)
    markup = dict_list_kb(dict_list)

    try:
        await call.message.edit_text(text=f"Справочник '{dict_class.hr_names['table_name']}' - {len(dict_list)}",
                                     disable_web_page_preview=True,
                                     reply_markup=markup)
    except Exception as err:
        logger.error("Error while deleting message. %r", err)


async def dict_get_name(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    async with state.proxy() as data:
        data["line_id"] = callback_data["line_id"]
        dict_id = int(data["dict_id"])
    dict_class = DICT_LIST[dict_id]
    await call.message.answer(f"Введите {dict_class.hr_names['name_name']}",
                              disable_web_page_preview=True,
                              reply_markup=ForceReply())
    await DctEdit.enter_name.set()
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.delete()


async def dict_enter_name(message: Message, state: FSMContext):
    await ChatActions.typing()
    Session = message.bot["Session"]
    try:
        dict_name = message.text
        async with state.proxy() as data:
            data["user_mention"] = message.from_user.mention
            dict_id = int(data["dict_id"])
            line_id = int(data["line_id"])
            data["dict_name"] = dict_name
        dict_class = DICT_LIST[dict_id]
        if dict_class.hr_names["type"] == DictType.SIMPLE:
            if line_id and line_id > 0:
                dict_obj = await dct_update(Session, dict_class, id=line_id, name=dict_name)
            else:
                dict_obj = await dct_create(Session, dict_class, name=dict_name)
            async with state.proxy() as data:
                data["line_id"] = dict_obj.id
            dict_list = await dct_list(Session, dict_class)
            markup = dict_list_kb(dict_list)
            await message.answer(text=f"Справочник '{dict_class.hr_names['table_name']}' - {len(dict_list)}",
                                 disable_web_page_preview=True,
                                 reply_markup=markup)
            await state.reset_state(with_data=False)
        elif dict_class.hr_names["type"] == DictType.COMPLEX:
            lookup_table = ERPMaterialType
            if dict_class.__name__ == "ERPMaterial":
                lookup_table = ERPMaterialType
            elif dict_class.__name__ == "ERPProduct":
                lookup_table = ERPProductType
            elif dict_class.__name__ == "ERPContractor":
                lookup_table = ERPCity
            lookup_list = await dct_list(Session, lookup_table, is_active=True)
            markup = lookup_kb(lookup_list)
            await message.answer(f"Выберите {dict_class.hr_names['lookup_name']}",
                                 disable_web_page_preview=True,
                                 reply_markup=markup)
            return
    except Exception as err:
        await state.reset_state(with_data=False)
        logger.error("Error while enter dict name. %r", err)


async def select_lookup(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    Session = call.message.bot["Session"]
    lookup_line_id = callback_data['line_id']
    async with state.proxy() as data:
        dict_id = int(data['dict_id'])
        dict_name = data['dict_name']
        line_id = int(data["line_id"])
    dict_class = DICT_LIST[dict_id]
    if dict_class.__name__ == "ERPMaterial":
        if line_id and line_id > 0:
            dict_obj = await dct_update(Session, dict_class,
                                        id=line_id,
                                        name=dict_name,
                                        material_type_id=lookup_line_id)
        else:
            dict_obj = await dct_create(Session, dict_class,
                                        name=dict_name,
                                        material_type_id=lookup_line_id)
    elif dict_class.__name__ == "ERPProduct":
        if line_id and line_id > 0:
            dict_obj = await dct_update(Session, dict_class,
                                        id=line_id,
                                        name=dict_name,
                                        product_type_id=lookup_line_id)
        else:
            dict_obj = await dct_create(Session, dict_class,
                                        name=dict_name,
                                        product_type_id=lookup_line_id)
    elif dict_class.__name__ == "ERPContractor":
        if line_id and line_id > 0:
            dict_obj = await dct_update(Session, dict_class,
                                        id=line_id,
                                        name=dict_name,
                                        city_id=lookup_line_id)
        else:
            dict_obj = await dct_create(Session, dict_class,
                                        name=dict_name,
                                        city_id=lookup_line_id)
    await state.reset_state(with_data=False)
    await dict_list_view(call, callback_data, state)


async def select_dict_record(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    Session = call.message.bot["Session"]
    async with state.proxy() as data:
        dict_id = int(data["dict_id"])
    dict_class = DICT_LIST[dict_id]
    line_id = int(callback_data["line_id"])

    dict_obj, message_text = await get_dict_text(Session, dict_class, line_id)
    markup = dict_edit_kb(dict_id, line_id, dict_obj.is_active)
    await call.message.edit_text(message_text,
                                 disable_web_page_preview=True,
                                 reply_markup=markup)
    async with state.proxy() as data:
        data["confirm_delete"] = False


async def dict_change_state(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    Session = call.message.bot["Session"]
    async with state.proxy() as data:
        dict_id = int(data["dict_id"])
    dict_class = DICT_LIST[dict_id]
    line_id = int(callback_data["line_id"])

    dict_obj = await dct_read(Session, dict_class, id=line_id)
    dict_obj = await dct_update(Session, dict_class, id=line_id, is_active=not dict_obj.is_active)
    dict_obj, message_text = await get_dict_text(Session, dict_class, line_id)
    markup = dict_edit_kb(dict_id, line_id, dict_obj.is_active)
    await call.message.edit_text(message_text,
                                 disable_web_page_preview=True,
                                 reply_markup=markup)


async def change_impurity(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    Session = call.message.bot["Session"]
    async with state.proxy() as data:
        dict_id = int(data["dict_id"])
    dict_class = DICT_LIST[dict_id]
    line_id = int(callback_data["line_id"])

    dict_obj = await dct_read(Session, dict_class, id=line_id)
    value = 0
    if callback_data["action"] == SimpleDictMenuAction.INC_IMPURITY:
        value = 1
    if callback_data["action"] == SimpleDictMenuAction.DEC_IMPURITY:
        value = -1
    dict_obj = await dct_update(Session, dict_class, id=line_id, impurity=dict_obj.impurity + value)
    dict_obj, message_text = await get_dict_text(Session, dict_class, line_id)
    markup = dict_edit_kb(dict_id, line_id, dict_obj.is_active)
    await call.message.edit_text(message_text,
                                 disable_web_page_preview=True,
                                 reply_markup=markup)


async def change_provider_state(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    Session = call.message.bot["Session"]
    async with state.proxy() as data:
        dict_id = int(data["dict_id"])
    dict_class = DICT_LIST[dict_id]
    line_id = int(callback_data["line_id"])

    dict_obj = await dct_read(Session, dict_class, id=line_id)
    dict_obj = await dct_update(Session, dict_class, id=line_id, is_provider=not dict_obj.is_provider)
    dict_obj, message_text = await get_dict_text(Session, dict_class, line_id)
    markup = dict_edit_kb(dict_id, line_id, dict_obj.is_active)
    await call.message.edit_text(message_text,
                                 disable_web_page_preview=True,
                                 reply_markup=markup)


async def change_buyer_state(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    Session = call.message.bot["Session"]
    async with state.proxy() as data:
        dict_id = int(data["dict_id"])
    dict_class = DICT_LIST[dict_id]
    line_id = int(callback_data["line_id"])

    dict_obj = await dct_read(Session, dict_class, id=line_id)
    dict_obj = await dct_update(Session, dict_class, id=line_id, is_buyer=not dict_obj.is_buyer)
    dict_obj, message_text = await get_dict_text(Session, dict_class, line_id)
    markup = dict_edit_kb(dict_id, line_id, dict_obj.is_active)
    await call.message.edit_text(message_text,
                                 disable_web_page_preview=True,
                                 reply_markup=markup)


async def delete_dict_record(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await ChatActions.typing()
    Session = call.message.bot["Session"]
    pprint(callback_data)
    async with state.proxy() as data:
        confirm_delete = int(data["confirm_delete"])
        dict_id = int(data["dict_id"])
        dict_class = DICT_LIST[dict_id]
        line_id = int(callback_data["line_id"])
        dict_obj, message_text = await get_dict_text(Session, dict_class, line_id)
        if confirm_delete:
            await dct_delete(Session, dict_class, id=line_id)
            data["confirm_delete"] = False
            await dict_list_view(call, callback_data, state)
            return
        else:
            data["confirm_delete"] = True

    callback_data_ok = dict_menu_data.new(action=SimpleDictMenuAction.DELETE_RECORD,
                                          line_id=line_id)
    callback_data_cancel = dict_menu_data.new(action=SimpleDictMenuAction.SELECT_RECORD,
                                              line_id=line_id)
    markup = confirm_kb(callback_data_ok, callback_data_cancel)
    await call.message.edit_text(message_text,
                                 disable_web_page_preview=True,
                                 reply_markup=markup)


def register_dict_setup(dp: Dispatcher):
    dp.register_message_handler(main_menu, commands=["dct"], state="*")
    dp.register_message_handler(dict_enter_name, state=DctEdit.enter_name)
    dp.register_callback_query_handler(main_menu_exit,
                                       main_menu_data.filter(action=MainMenuAction.MM_EXIT),
                                       state="*")
    dp.register_callback_query_handler(dict_list_view,
                                       main_menu_data.filter(action=MainMenuAction.MM_SELECT_DICT),
                                       state="*")
    dp.register_callback_query_handler(back_to_main_menu,
                                       main_menu_data.filter(action=MainMenuAction.MM_RETURN_TO_MM),
                                       state="*")
    dp.register_callback_query_handler(dict_get_name,
                                       dict_menu_data.filter(action=[SimpleDictMenuAction.NEW_RECORD,
                                                                     SimpleDictMenuAction.EDIT_NAME]),
                                       state="*")
    dp.register_callback_query_handler(select_dict_record,
                                       dict_menu_data.filter(action=SimpleDictMenuAction.SELECT_RECORD),
                                       state="*")
    dp.register_callback_query_handler(dict_change_state,
                                       dict_menu_data.filter(action=SimpleDictMenuAction.CHANGE_STATE),
                                       state="*")
    dp.register_callback_query_handler(change_provider_state,
                                       dict_menu_data.filter(action=SimpleDictMenuAction.CHANGE_PROVIDER_STATE),
                                       state="*")
    dp.register_callback_query_handler(change_buyer_state,
                                       dict_menu_data.filter(action=SimpleDictMenuAction.CHANGE_BUYER_STATE),
                                       state="*")
    dp.register_callback_query_handler(change_impurity,
                                       dict_menu_data.filter(action=[SimpleDictMenuAction.INC_IMPURITY,
                                                                     SimpleDictMenuAction.DEC_IMPURITY]),
                                       state="*")
    dp.register_callback_query_handler(delete_dict_record,
                                       dict_menu_data.filter(action=SimpleDictMenuAction.DELETE_RECORD),
                                       state="*")
    dp.register_callback_query_handler(select_lookup,
                                       dict_menu_data.filter(action=SimpleDictMenuAction.SELECT_LOOKUP),
                                       state="*")
