from dataclasses import dataclass
from pprint import pprint
from typing import List

from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData


class ShiftMultiselect(StatesGroup):
    select_staff = State()
    select_activity = State()
    select_materials = State()
    select_products = State()


class ShiftNavigator(StatesGroup):
    shift_go_to = State()
    shift_date_selected = State()


class ShiftEnterValue(StatesGroup):
    material_weight = State()
    product_bag = State()
    product_weight = State()


@dataclass(frozen=True)
class ShiftMenuAction:
    SM_SHIFT_ACTIVITY: str = 'sm0'
    SM_SHIFT_EXIT: str = 'sm1'
    SM_SHIFT_GOTO: str = 'sm2'
    SM_SHIFT_MATERIAL: str = 'sm3'
    SM_SHIFT_NEW: str = 'sm4'
    SM_SHIFT_NEXT: str = 'sm5'
    SM_SHIFT_PREV: str = 'sm6'
    SM_SHIFT_PRODUCT: str = 'sm7'
    SM_SHIFT_STAFF: str = 'sm8'
    SM_SHIFT_SELECT: str = 'sm9'
    SM_IGNORE: str = 'sm99'
    SM_CANCEL: str = 'sm00'


@dataclass(frozen=True)
class ShiftLookupAction:
    SL_LOOKUP_SELECT: str = 'sl0'
    SL_LOOKUP_CONFIRM: str = 'sl1'
    SL_LOOKUP_CANCEL: str = 'sl2'


@dataclass(frozen=True)
class ChangeNumericValue:
    CNV_INC: str = 'cnv01'
    CNV_DEC: str = 'cnv02'
    CNV_CONFIRM: str = 'cnv03'
    CNV_CANCEL: str = 'cnv04'


@dataclass(frozen=True)
class NumericKb:
    NUM_CONFIRM: str = 'nkb01'
    NUM_CANCEL: str = 'nkb02'


@dataclass(frozen=True)
class SelectEditData:
    SED_BAG_NUMBER: str = 'sed00'
    SED_WEIGHT: str = 'sed01'
    SED_BACK: str = 'sed02'


def chunks_generators(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i: i + n]


shift_menu_data = CallbackData("sma", "action", "shift_number")
shift_lookup_data = CallbackData("sla", "action", "item_id")
change_numeric_value = CallbackData("cnv", "action")
numeric_kb_data = CallbackData("num", "key_value")
select_edit_data = CallbackData("edd", "key_value")


def shift_kb(navigate: bool) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    button_new = InlineKeyboardButton(text="➕",
                                      callback_data=shift_menu_data.new(
                                          action=ShiftMenuAction.SM_SHIFT_NEW,
                                          shift_number=-1))
    button_goto = InlineKeyboardButton(text="#️⃣",
                                       callback_data=shift_menu_data.new(
                                           action=ShiftMenuAction.SM_SHIFT_GOTO,
                                           shift_number=-1))
    button_exit = InlineKeyboardButton(text="✋",
                                       callback_data=shift_menu_data.new(
                                           action=ShiftMenuAction.SM_SHIFT_EXIT,
                                           shift_number=-1))
    buttons = [button_new, button_goto, button_exit]

    if navigate:
        markup.row(InlineKeyboardButton(text="💎 Сырье",
                                        callback_data=shift_menu_data.new(
                                            action=ShiftMenuAction.SM_SHIFT_MATERIAL,
                                            shift_number=-1)),
                   InlineKeyboardButton(text="🎁 Продукция",
                                        callback_data=shift_menu_data.new(
                                            action=ShiftMenuAction.SM_SHIFT_PRODUCT,
                                            shift_number=-1)))
        markup.row(InlineKeyboardButton(text="◀️",
                                        callback_data=shift_menu_data.new(
                                            action=ShiftMenuAction.SM_SHIFT_PREV,
                                            shift_number=-1)),
                   InlineKeyboardButton(text="▶️",
                                        callback_data=shift_menu_data.new(
                                            action=ShiftMenuAction.SM_SHIFT_NEXT,
                                            shift_number=-1)))
    else:
        buttons.pop(1)

    markup.row(*buttons)

    return markup


def multi_select_list_kb(source_list: list, selected_items: list, row_width=1) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=row_width)
    row_buttons = (InlineKeyboardButton(text="✅ " + item.name if item.id in selected_items else item.name,
                                        callback_data=shift_lookup_data.new(action=ShiftLookupAction.SL_LOOKUP_SELECT,
                                                                            item_id=item.id)) for item in source_list)
    _ = list(markup.insert(button) for button in row_buttons)
    row_buttons = [InlineKeyboardButton(text="🟢 Выбрать",
                                        callback_data=shift_lookup_data.new(
                                            action=ShiftLookupAction.SL_LOOKUP_CONFIRM,
                                            item_id=-1)),
                   InlineKeyboardButton(text="❌ Отменить",
                                        callback_data=shift_lookup_data.new(
                                            action=ShiftLookupAction.SL_LOOKUP_CANCEL,
                                            item_id=-1))
                   ]
    if not len(selected_items):
        row_buttons.pop(0)
    markup.row(*row_buttons)
    return markup


def select_shift_kb(completed_shifts: List[int]) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=3)
    for num in range(1, 4):
        button_text = "⚫️ " + str(num) if num in completed_shifts else "🔘 " + str(num)
        button_action = ShiftMenuAction.SM_IGNORE if num in completed_shifts else ShiftMenuAction.SM_SHIFT_SELECT
        button = InlineKeyboardButton(text=button_text,
                                      callback_data=shift_menu_data.new(action=button_action,
                                                                        shift_number=num))
        markup.insert(button)
    markup.row(InlineKeyboardButton(text="Отменить",
                                    callback_data=shift_menu_data.new(action=ShiftMenuAction.SM_CANCEL,
                                                                      shift_number=-1)))
    return markup


def change_numeric_value_kb() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    markup.row(InlineKeyboardButton(text="➕",
                                    callback_data=change_numeric_value.new(action=ChangeNumericValue.CNV_INC)),
               InlineKeyboardButton(text="➖",
                                    callback_data=change_numeric_value.new(action=ChangeNumericValue.CNV_DEC)))
    markup.row(InlineKeyboardButton(text="✅",
                                    callback_data=change_numeric_value.new(action=ChangeNumericValue.CNV_CONFIRM)),
               InlineKeyboardButton(text="❌",
                                    callback_data=change_numeric_value.new(action=ChangeNumericValue.CNV_CANCEL)))
    return markup


def numeric_kb() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=3)
    markup.row(InlineKeyboardButton(text="Сброс",
                                    callback_data=numeric_kb_data.new(key_value="clear")),
               InlineKeyboardButton(text="<-",
                                    callback_data=numeric_kb_data.new(key_value="backspace")))
    row_buttons = (InlineKeyboardButton(text=str(k),
                                        callback_data=numeric_kb_data.new(key_value=i)) for i in range(3, -1, -1)
                   for k in range(i * i - 2 * (i - 2) if i >= 2 else i, i * i - 2 * (i - 2) + 3 if i >= 2 else i + 3)
                   if not (i == 0 and k > 0))
    _ = list(markup.row(*row) for row in list(chunks_generators(list(row_buttons), 3)))

    markup.insert(InlineKeyboardButton(text=".",
                                       callback_data=numeric_kb_data.new(key_value="dot")))
    markup.row(InlineKeyboardButton(text="✅",
                                    callback_data=numeric_kb_data.new(key_value="ok")),
               InlineKeyboardButton(text="❌",
                                    callback_data=numeric_kb_data.new(key_value="cancel")))
    return markup


def select_edit_data_kb() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    markup.row(InlineKeyboardButton(text="Номер мешка",
                                    callback_data=select_edit_data.new(key_value=SelectEditData.SED_BAG_NUMBER)),
               InlineKeyboardButton(text="Вес",
                                    callback_data=select_edit_data.new(key_value=SelectEditData.SED_WEIGHT)))
    markup.row(InlineKeyboardButton(text="<<",
                                    callback_data=select_edit_data.new(key_value=SelectEditData.SED_BACK)))
    return markup
