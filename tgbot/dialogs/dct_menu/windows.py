from . import keyboards, states, onclick, getters, events, constants, whenables
from .keyboards import dct_items_kbd
from ...widgets.aiogram_dialog import Window
from ...widgets.aiogram_dialog.widgets.input import TextInput
from ...widgets.aiogram_dialog.widgets.kbd import Cancel, Row, Checkbox, Button, SwitchTo, Back
from ...widgets.aiogram_dialog.widgets.text import Const, Format


def dct_menu_window():
    return Window(
        Const("Справочники"),
        keyboards.dct_list_kbd(on_click=onclick.on_select_dct),
        Cancel(Const("<<")),
        state=states.DictMenuStates.select_dct
    )


def show_dct_window(state):
    return Window(
        Format(text="{dct_action} {dct_name}"),
        dct_items_kbd(on_click=onclick.on_dct_item_selected),
        Row(Back(Const("<<")),
            Button(Const("＋"),
                   id=constants.DctMenuIds.ADD_DCT_ITEM,
                   on_click=onclick.on_new_dct_item),
            when=whenables.is_show_mode),
        state=state,
        getter=getters.get_dct_items
    )


def show_dct_item_window():
    return Window(
        Format(text="{dct_item}"),
        Row(Checkbox(Const("🔔"),
                     Const("🔕"),
                     id=constants.DctMenuIds.DCT_ITEM_STATE,
                     on_state_changed=events.dct_item_state_changed,
                     default=True),
            Button(Const("✍️"),
                   id=constants.DctMenuIds.DCT_ITEM_EDIT_BUTTON,
                   on_click=onclick.on_edit_dct_item),
            Button(Const("🔢"),
                   id=constants.DctMenuIds.DCT_ITEM_EDIT_DIGITAL_VALUE,
                   on_click=onclick.on_edit_dct_item,
                   when=whenables.is_material),
            Checkbox(Const("🚛 ✓"),
                     Const("🚛 ☐ "),
                     id=constants.DctMenuIds.IS_PROVIDER_STATE,
                     on_state_changed=events.dct_item_state_changed,
                     default=True,
                     when=whenables.is_contractor),
            Checkbox(Const("🛒 ✓"),
                     Const("🛒 ☐ "),
                     id=constants.DctMenuIds.IS_BUYER_STATE,
                     on_state_changed=events.dct_item_state_changed,
                     default=True,
                     when=whenables.is_contractor),
            Button(Const("❌"),
                   id=constants.DctMenuIds.DCT_ITEM_DELETE_BUTTON,
                   on_click=onclick.on_delete_dct_item),
            SwitchTo(Const("<<"),
                     id=constants.DctMenuIds.SWITCH_TO_SHOW_DCT,
                     state=states.DictMenuStates.show_dct),
            ),
        state=states.DictMenuStates.show_dct_item,
        getter=getters.get_dct_item
    )


def set_dct_item_window():
    return Window(
        Format("{dct_item}"),
        TextInput(id=constants.DctMenuIds.DCT_ITEM_CONTENT,
                  type_factory=str,
                  on_error=events.on_error_enter_dct_item,
                  on_success=events.on_success_enter_dct_item),
        state=states.DictMenuStates.edit_dct_item,
        getter=getters.get_dct_item
    )
