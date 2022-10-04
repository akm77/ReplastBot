from datetime import date, datetime
from zoneinfo import ZoneInfo

from aiogram.types import InlineKeyboardButton, CallbackQuery

from tgbot.widgets.aiogram_datepicker import DatepickerCustomAction, DatepickerSettings


def get_datepicker_settings():
    class CancelAction(DatepickerCustomAction):
        action: str = 'cancel'
        label: str = 'Отмена'

        def get_action(self, view: str, year: int, month: int, day: int) -> InlineKeyboardButton:
            return InlineKeyboardButton(self.label,
                                        callback_data=self._get_callback(view, self.action, year, month, day))

        async def process(self, query: CallbackQuery, view: str, _date: date) -> bool:
            if view == 'day':
                await query.message.delete()
                return False

    return DatepickerSettings(
        initial_view='day',
        initial_date=datetime.now(tz=ZoneInfo("Asia/Vladivostok")).date(),
        views={
            'day': {
                'show_weekdays': True,
                'weekdays_labels': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
                'header': ['prev-year', 'days-title', 'next-year'],
                'footer': ['prev-month', 'select', 'next-month', ['cancel']],
                'locale': ('ru_RU', 'UTF-8'),
                'tzinfo': 'Asia/Vladivostok'
            },
            'month': {
                'months_labels': ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'],
                'header': ['prev-year', 'year', 'next-year'],
                'footer': []
            },
            'year': {
                'header': [],
                'footer': ['prev-years', 'next-years']
            }
        },
        labels={
            'prev-year': '<<',
            'next-year': '>>',
            'prev-years': '<<',
            'next-years': '>>',
            'days-title': '{month} {year}',
            'selected-day': '{day} *',
            'selected-month': '{month} *',
            'present-day': '• {day} •',
            'prev-month': '<',
            'select': 'Выбрать',
            'next-month': '>',
            'ignore': '⠀'
        },
        custom_actions=[CancelAction]
    )
