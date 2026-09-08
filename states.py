from aiogram.fsm.state import State, StatesGroup


class SettingsStates(StatesGroup):
    waiting_bg_color = State()
    waiting_resolution = State()
    waiting_recolor = State()
    waiting_custom_media = State()
    waiting_wm_text = State()
    waiting_wm_color = State()
