from typing import Dict

from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.when import Whenable


def is_selecting_date(data: Dict, widget: Whenable, manager: DialogManager):
    wd = widget
    mgr = manager
    return data.get("date_selecting")
