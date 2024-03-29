import datetime
from abc import ABC
from calendar import monthcalendar, different_locale, day_abbr, month_abbr
from datetime import date
from time import mktime
from typing import List, Callable, Union, Awaitable, TypedDict, Optional
from zoneinfo import ZoneInfo

from aiogram.types import InlineKeyboardButton, CallbackQuery

from .base import Keyboard
from ..managed import ManagedWidgetAdapter
from ...context.events import ChatEvent
from ...deprecation_utils import manager_deprecated
from ...manager.protocols import DialogManager, ManagedDialogProto
from ...widgets.widget_event import WidgetEventProcessor, \
    ensure_event_processor

OnDateSelected = Callable[[ChatEvent, "ManagedCalendarAdapter", DialogManager, date], Awaitable]
SetMarkedDate = Callable[[ChatEvent, "ManagedCalendarAdapter", DialogManager, date], Awaitable]

# Constants for managing widget rendering scope
SCOPE_DAYS = "SCOPE_DAYS"
SCOPE_MONTHS = "SCOPE_MONTHS"
SCOPE_YEARS = "SCOPE_YEARS"

# Constants for scrolling months
MONTH_NEXT = "+"
MONTH_PREV = "-"

# Constants for prefixing month and year values
PREFIX_MONTH = "MONTH"
PREFIX_YEAR = "YEAR"

MONTHS_NUMBERS = [(1, 2, 3), (4, 5, 6), (7, 8, 9), (10, 11, 12)]


class CalendarData(TypedDict):
    current_scope: str
    current_offset: str


class Calendar(Keyboard, ABC):
    def __init__(self,
                 id: str,
                 on_click: Union[OnDateSelected, WidgetEventProcessor, None] = None,
                 marked_day: Union[datetime.date, datetime.datetime, Callable, None] = None,
                 when: Union[str, Callable] = None,
                 tz: str = "UTC",
                 calendar_locale=(None, None)):
        super().__init__(id, when)
        self.tzinfo = ZoneInfo(tz)
        self.calendar_locale = calendar_locale
        self.on_click = ensure_event_processor(on_click)
        self.marked_day = None
        self.__marked_day_getter = None
        if isinstance(marked_day, datetime.date):
            self.marked_day = marked_day
        elif isinstance(marked_day, datetime.datetime):
            self.marked_day = marked_day.date()
        elif isinstance(marked_day, Callable):
            self.__marked_day_getter = marked_day

    async def _render_keyboard(self,
                               data,
                               manager: DialogManager) -> List[List[InlineKeyboardButton]]:
        if self.__marked_day_getter and isinstance(self.__marked_day_getter, Callable):
            self.marked_day = self.__marked_day_getter(manager)
            if not isinstance(self.marked_day, datetime.date):
                self.marked_day = None
        offset = self.get_offset(manager)
        current_scope = self.get_scope(manager)

        if current_scope == SCOPE_DAYS:
            return self.days_kbd(offset)
        elif current_scope == SCOPE_MONTHS:
            return self.months_kbd(offset)
        elif current_scope == SCOPE_YEARS:
            return self.years_kbd(offset)

    async def _process_item_callback(
            self, c: CallbackQuery, data: str, dialog: ManagedDialogProto,
            manager: DialogManager,
    ) -> bool:
        current_offset = self.get_offset(manager)

        if data == MONTH_NEXT:
            new_offset = date(
                year=current_offset.year + (current_offset.month // 12),
                month=((current_offset.month % 12) + 1),
                day=1,
            )
            self.set_offset(new_offset, manager)

        elif data == MONTH_PREV:
            if current_offset.month == 1:
                new_offset = date(current_offset.year - 1, 12, 1)
                self.set_offset(new_offset, manager)
            else:
                new_offset = date(current_offset.year, (current_offset.month - 1), 1)
                self.set_offset(new_offset, manager)

        elif data in [SCOPE_MONTHS, SCOPE_YEARS]:
            self.set_scope(data, manager)

        elif data.startswith(PREFIX_MONTH):
            data = int(data[len(PREFIX_MONTH):])
            new_offset = date(current_offset.year, data, 1)
            self.set_scope(SCOPE_DAYS, manager)
            self.set_offset(new_offset, manager)

        elif data.startswith(PREFIX_YEAR):
            data = int(data[len(PREFIX_YEAR):])
            new_offset = date(data, 1, 1)
            self.set_scope(SCOPE_MONTHS, manager)
            self.set_offset(new_offset, manager)

        else:
            raw_date = int(data)
            await self.on_click.process_event(
                c, self.managed(manager), manager,
                date.fromtimestamp(raw_date),
            )
        return True

    def years_kbd(self, offset) -> List[List[InlineKeyboardButton]]:
        years = []
        for n in range(offset.year - 7, offset.year + 7, 3):
            year_row = []
            for year in range(n, n + 3):
                year_row.append(InlineKeyboardButton(
                    text=str(year),
                    callback_data=self._item_callback_data(f"{PREFIX_YEAR}{year}")
                ))
            years.append(year_row)
        return years

    def months_kbd(self, offset) -> List[List[InlineKeyboardButton]]:
        header_year = offset.strftime("%Y")
        months = []
        for n in MONTHS_NUMBERS:
            season = []
            with different_locale(self.calendar_locale):
                for month in n:
                    month_text = month_abbr[month]
                    season.append(InlineKeyboardButton(
                        text=month_text,
                        callback_data=self._item_callback_data(f"{PREFIX_MONTH}{month}"))
                    )
            months.append(season)
        return [
            [
                InlineKeyboardButton(
                    text=header_year,
                    callback_data=self._item_callback_data(SCOPE_YEARS),
                ),
            ],
            *months
        ]

    def days_kbd(self, offset) -> List[List[InlineKeyboardButton]]:
        with different_locale(self.calendar_locale):
            header_week = month_abbr[offset.month] + offset.strftime(" %Y")
            weekheader = [
                InlineKeyboardButton(text=dayname, callback_data=" ")
                for dayname in day_abbr
            ]
        days = []
        for week in monthcalendar(offset.year, offset.month):
            week_row = []
            for day in week:
                if day == 0:
                    week_row.append(InlineKeyboardButton(
                        text=" ",
                        callback_data=" ",
                    ))
                else:
                    current_day = datetime.datetime.now(tz=self.tzinfo).date()
                    raw_current_date = int(mktime(date(current_day.year,
                                                       current_day.month,
                                                       current_day.day).timetuple()))
                    raw_marked_day = int(mktime(date(self.marked_day.year,
                                                     self.marked_day.month,
                                                     self.marked_day.day).timetuple())) if self.marked_day else 0
                    raw_date = int(mktime(date(offset.year, offset.month, day).timetuple()))
                    if raw_current_date == raw_date:
                        button_text = f"{day}*"
                    elif raw_marked_day == raw_date:
                        button_text = f"{day}✓"
                    else:
                        button_text = str(day)
                    week_row.append(InlineKeyboardButton(
                        text=button_text,
                        callback_data=self._item_callback_data(raw_date),
                    ))
            days.append(week_row)
        return [
            [
                InlineKeyboardButton(
                    text=header_week,
                    callback_data=self._item_callback_data(SCOPE_MONTHS),
                ),
            ],
            weekheader,
            *days,
            [
                InlineKeyboardButton(
                    text="<",
                    callback_data=self._item_callback_data(MONTH_PREV),
                ),
                InlineKeyboardButton(
                    text="<>",
                    callback_data=self._item_callback_data(SCOPE_MONTHS),
                ),
                InlineKeyboardButton(
                    text=">",
                    callback_data=self._item_callback_data(MONTH_NEXT),
                ),
            ],
        ]

    def get_scope(self, manager: DialogManager) -> str:
        calendar_data: CalendarData = self.get_widget_data(manager, {})
        current_scope = calendar_data.get("current_scope")
        return current_scope or SCOPE_DAYS

    def get_offset(self, manager: DialogManager) -> date:
        calendar_data: CalendarData = self.get_widget_data(manager, {})
        current_offset = calendar_data.get("current_offset")
        if current_offset is None:
            return datetime.datetime.now(tz=self.tzinfo).date()
        return date.fromisoformat(current_offset)

    def set_offset(self, new_offset: date, manager: DialogManager) -> None:
        data = self.get_widget_data(manager, {})
        data["current_offset"] = new_offset.isoformat()

    def set_scope(self, new_scope: str, manager: DialogManager) -> None:
        data = self.get_widget_data(manager, {})
        data["current_scope"] = new_scope

    def managed(self, manager: DialogManager):
        return ManagedCalendarAdapter(self, manager)


class ManagedCalendarAdapter(ManagedWidgetAdapter[Calendar]):
    def get_scope(self, manager: Optional[DialogManager] = None) -> str:
        manager_deprecated(manager)
        return self.widget.get_scope(self.manager)

    def get_offset(self, manager: Optional[DialogManager] = None) -> date:
        manager_deprecated(manager)
        return self.widget.get_offset(self.manager)

    def set_offset(self, new_offset: date,
                   manager: Optional[DialogManager] = None) -> None:
        manager_deprecated(manager)
        return self.widget.set_offset(new_offset, self.manager)

    def set_scope(self, new_scope: str,
                  manager: Optional[DialogManager] = None) -> None:
        manager_deprecated(manager)
        return self.widget.set_scope(new_scope, self.manager)
