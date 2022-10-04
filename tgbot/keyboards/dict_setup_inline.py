from dataclasses import dataclass

from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from tgbot.misc.utils import chunks_generators
from tgbot.models.erp_dict import DICT_LIST, DictType


class DctEdit(StatesGroup):
    enter_name = State()
    enter_lookup_field = State()
    enter_impurity = State()


@dataclass(frozen=True)
class MainMenuAction:
    MM_EXIT: str = 'mm0'
    MM_SELECT_DICT: str = 'mm1'
    MM_RETURN_TO_MM: str = 'mm2'


main_menu_data = CallbackData("mma", "action", "dict_id")


@dataclass(frozen=True)
class SimpleDictMenuAction:
    NEW_RECORD: str = 'sd0'
    SELECT_RECORD: str = 'sd1'
    EDIT_NAME: str = 'sd2'
    CHANGE_STATE: str = 'sd3'
    DELETE_RECORD: str = 'sd4'
    SELECT_LOOKUP: str = 'sd5'
    INC_IMPURITY: str = 'sd6'
    DEC_IMPURITY: str = 'sd7'
    CHANGE_PROVIDER_STATE: str = 'sd8'
    CHANGE_BUYER_STATE: str = 'sd9'


dict_menu_data = CallbackData("sdma", "action", "line_id")


def confirm_kb(callback_data_ok, callback_data_cancel) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton(text="Удалить ⁉️", callback_data=callback_data_ok),
               InlineKeyboardButton(text="<<", callback_data=callback_data_cancel))
    return markup


def main_menu_kb() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    row_buttons = (InlineKeyboardButton(text=dct.hr_names["table_name"],
                                        callback_data=main_menu_data.new(
                                            action=MainMenuAction.MM_SELECT_DICT,
                                            dict_id=i)) for i, dct in enumerate(DICT_LIST))
    _ = list(markup.row(*row) for row in list(chunks_generators(list(row_buttons), 2)))
    markup.row(InlineKeyboardButton(text="👋 Выход",
                                    callback_data=main_menu_data.new(
                                        action=MainMenuAction.MM_EXIT,
                                        dict_id=0)))
    return markup


def dict_list_kb(dict_list) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=1)
    for line in dict_list:
        kb_text = f"{'🔔' if line.is_active else '🔕'} {line.name} (#{line.id})"
        markup.row(InlineKeyboardButton(text=kb_text,
                                        callback_data=dict_menu_data.new(
                                            action=SimpleDictMenuAction.SELECT_RECORD,
                                            line_id=line.id)))
    markup.row(InlineKeyboardButton(text="❇️ Новый",
                                    callback_data=dict_menu_data.new(action=SimpleDictMenuAction.NEW_RECORD,
                                                                     line_id=0)),
               InlineKeyboardButton(text="👋 Выход",
                                    callback_data=main_menu_data.new(action=MainMenuAction.MM_RETURN_TO_MM,
                                                                     dict_id=0)))
    return markup


def dict_edit_kb(dict_id, line_id, is_active) -> InlineKeyboardMarkup:
    dict_class = DICT_LIST[dict_id]
    button_new = InlineKeyboardButton(text="🔕" if is_active else "🔔",
                                      callback_data=dict_menu_data.new(
                                          action=SimpleDictMenuAction.CHANGE_STATE,
                                          line_id=line_id))
    button_edit_name = InlineKeyboardButton(text="📝",
                                            callback_data=dict_menu_data.new(
                                                action=SimpleDictMenuAction.EDIT_NAME,
                                                line_id=line_id))
    button_delete = InlineKeyboardButton(text="❌",
                                         callback_data=dict_menu_data.new(
                                             action=SimpleDictMenuAction.DELETE_RECORD,
                                             line_id=line_id))
    button_back = InlineKeyboardButton(text="<<",
                                       callback_data=main_menu_data.new(
                                           action=MainMenuAction.MM_SELECT_DICT,
                                           dict_id=dict_id))
    buttons = [button_new, button_edit_name]
    if dict_class.__name__ == "ERPMaterial":
        button_inc = InlineKeyboardButton(text="➕",
                                          callback_data=dict_menu_data.new(
                                              action=SimpleDictMenuAction.INC_IMPURITY,
                                              line_id=line_id))
        button_dec = InlineKeyboardButton(text="➖",
                                          callback_data=dict_menu_data.new(
                                              action=SimpleDictMenuAction.DEC_IMPURITY,
                                              line_id=line_id))
        buttons.append(button_inc)
        buttons.append(button_dec)
    elif dict_class.__name__ == "ERPContractor":
        button_is_provider = InlineKeyboardButton(text="🎁",
                                                  callback_data=dict_menu_data.new(
                                                      action=SimpleDictMenuAction.CHANGE_PROVIDER_STATE,
                                                      line_id=line_id))
        button_is_buyer = InlineKeyboardButton(text="🛒",
                                               callback_data=dict_menu_data.new(
                                                   action=SimpleDictMenuAction.CHANGE_BUYER_STATE,
                                                   line_id=line_id))
        buttons.append(button_is_provider)
        buttons.append(button_is_buyer)

    buttons.append(button_delete)
    buttons.append(button_back)
    markup = InlineKeyboardMarkup()
    markup.row(*buttons)
    return markup


def lookup_kb(lookup_list) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    row_buttons = (InlineKeyboardButton(text=line.name,
                                        callback_data=dict_menu_data.new(
                                            action=SimpleDictMenuAction.SELECT_LOOKUP,
                                            line_id=line.id)) for line in lookup_list)
    _ = list(markup.row(*row) for row in list(chunks_generators(list(row_buttons), 2)))
    return markup
