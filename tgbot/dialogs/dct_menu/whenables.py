from typing import Dict

from . import states
from ...widgets.aiogram_dialog import DialogManager
from ...widgets.aiogram_dialog.widgets.when import Whenable


def is_material(data: Dict, widget: Whenable, manager: DialogManager):
    return data.get("dialog_data").get("dct") == "ERPMaterial"


def is_contractor(data: Dict, widget: Whenable, manager: DialogManager):
    return data.get("dialog_data").get("dct") == "ERPContractor"


def is_show_mode(data: Dict, widget: Whenable, manager: DialogManager):
    ctx = manager.current_context()
    return ctx.state == states.DictMenuStates.show_dct
