from aiogram.fsm.state import State, StatesGroup

# Обычная группа состояний


class startSG(StatesGroup):
    start = State()

    get_base_name = State()
    bases = State()
    del_base_confirm = State()
    base = State()

    channels = State()
    get_base_channel = State()
    del_channel = State()
    del_channel_confirm = State()

    accounts = State()
    del_account = State()
    del_account_confirm =State()
    get_name = State()
    choose_account_type = State()
    add_account = State()
    kod_send = State()
    get_password = State()


class adminSG(StatesGroup):
    start = State()
    admin_menu = State()
    admin_del = State()
    admin_add = State()
