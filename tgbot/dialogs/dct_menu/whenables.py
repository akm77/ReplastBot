from typing import Dict

from ...widgets.aiogram_dialog import DialogManager
from ...widgets.aiogram_dialog.widgets.when import Whenable


def is_material(data: Dict, widget: Whenable, manager: DialogManager):
    return data.get("name") == "Tishka17"