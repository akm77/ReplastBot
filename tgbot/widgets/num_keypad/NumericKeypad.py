from decimal import Decimal
from typing import Optional, Union

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.callback_data import CallbackData


class NumericKeypad:
    callback = CallbackData("num_keypad", "key_value", "value")

    def __init__(self, initial_value: Union[str, int, float, Decimal] = "0", message_text: str = None) -> None:
        self.__message_text = self.__check_message_text(message_text)
        self.__message_text = self.__message_text if "/*value*/" in self.__message_text else \
            self.__message_text + "/*value*/"
        self.__initial_value = initial_value
        self.__value = self.__check_input_value(initial_value)

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        self.__value = self.__check_input_value(value)

    @property
    def message_text(self):
        return self.__message_text

    @message_text.setter
    def message_text(self, value):
        self.__message_text = self.__check_message_text(value)

    @staticmethod
    def chunks_generator(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i: i + n]

    @staticmethod
    def __check_input_value(value: Union[str, int, float, Decimal]) -> Optional[str]:
        if isinstance(value, (int, float, Decimal)):
            return str(value)
        if isinstance(value, str):
            try:
                _ = Decimal(value if len(value) > 0 else "0")
                return value
            except Exception:
                raise Exception

    @staticmethod
    def __check_message_text(value: str) -> Optional[str]:
        message_text = "/*value*/" if value is None else value
        return message_text if "/*value*/" in message_text else message_text + "/*value*/"

    def start(self) -> InlineKeyboardMarkup:
        return self.get_markup(self.__initial_value)

    def get_markup(self, value) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup(row_width=3)
        markup.row(InlineKeyboardButton(text="Сброс",
                                        callback_data=self.callback.new(key_value="clear", value=value)),
                   InlineKeyboardButton(text="<-",
                                        callback_data=self.callback.new(key_value="backspace", value=value)))
        row_buttons = (InlineKeyboardButton(text=str(k),
                                            callback_data=self.callback.new(key_value=k,
                                                                            value=value)) for i in range(3, -1, -1)
                       for k in
                       range(i * i - 2 * (i - 2) if i >= 2 else i, i * i - 2 * (i - 2) + 3 if i >= 2 else i + 3)
                       if not (i == 0 and k > 0))
        _ = list(markup.row(*row) for row in list(self.chunks_generator(list(row_buttons), 3)))

        markup.insert(InlineKeyboardButton(text=".",
                                           callback_data=self.callback.new(key_value="dot", value=value)))
        markup.row(InlineKeyboardButton(text="✅",
                                        callback_data=self.callback.new(key_value="ok", value=value)),
                   InlineKeyboardButton(text="❌",
                                        callback_data=self.callback.new(key_value="cancel", value=value)))
        return markup

    async def process(self, call: CallbackQuery, data: dict) -> Optional[str]:
        key_value = data["key_value"]
        self.__value = data["value"]
        if key_value == "cancel":
            return self.__initial_value
        elif key_value == "ok":
            return self.__value
        elif key_value == "clear":
            self.__value = "0"
        elif key_value == "backspace":
            self.__value = "0" if len(self.__value) == 1 else self.__value[:-1]
        elif key_value == "dot":
            if "." in self.__value:
                return
            self.__value += "."
        else:
            if self.__value == "0" and key_value == "0":
                return
            elif self.__value == "0" and key_value != "0":
                self.__value = key_value
            else:
                self.__value = self.__value + key_value

        await call.message.edit_text(self.__message_text.replace("/*value*/", self.__value),
                                     reply_markup=self.get_markup(self.__value))
