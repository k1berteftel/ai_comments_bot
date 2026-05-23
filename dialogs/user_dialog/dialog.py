from aiogram.types import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import SwitchTo, Column, Row, Button, Group, Select, Start, Url, Back
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.media import DynamicMedia

from dialogs.user_dialog import getters

from states.state_groups import startSG, adminSG

user_dialog = Dialog(
    Window(
        Const('Главное меню'),
        Column(
            SwitchTo(Const('Добавить базу'), id='get_base_name_switcher', state=startSG.get_base_name),
            #SwitchTo(Const('Удалить базу'), id='del_base_switcher', state=startSG.del_base),
            SwitchTo(Const('Управление базами'), id='bases_switcher', state=startSG.bases),
            Start(Const('Админ панель'), id='admin', state=adminSG.start, when='admin'),
            #SwitchTo(Const('👥Управление аккаунтами'), id='accounts_switcher', state=startSG.accounts),
        ),
        getter=getters.start_getter,
        state=startSG.start
    ),
    Window(
        Const('Введите название для базы'),
        TextInput(
            id='get_base_name',
            on_success=getters.get_base_name
        ),
        SwitchTo(Const('⬅️Назад'), id='back', state=startSG.start),
        state=startSG.get_base_name
    ),
    Window(
        Const('Выберите базу, которую вы хотели бы открыть'),
        Group(
            Select(
                Format('{item[0]}'),
                id='bases_getters',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.base_select
            ),
            width=1
        ),
        SwitchTo(Const('⬅️Назад'), id='back', state=startSG.start),
        getter=getters.bases_getter,
        state=startSG.bases
    ),
    Window(
        Format('База номер <b>{base_id}</b> "{name}"\n{channels}\n{accounts}'),
        Column(
            SwitchTo(Const('Управление каналами'), id='channels_switcher', state=startSG.channels),
            SwitchTo(Const('Управление аккаунтами (ботами)'), id='accounts_switcher', state=startSG.accounts),
            SwitchTo(Const('Удалить базу'), id='del_base_switcher', state=startSG.del_base_confirm),
        ),
        SwitchTo(Const('⬅️Назад'), id='back', state=startSG.start),
        getter=getters.base_getter,
        state=startSG.base
    ),
    Window(
        Const('Вы действительно хотите удалить данную базу?'),
        Row(
            Button(Const('Удалить'), id='del_base', on_click=getters.del_base),
            SwitchTo(Const('Отмена'), id='back_base', state=startSG.base),
        ),
        state=startSG.del_base_confirm
    ),
    Window(
        Format('Каналы для базы "{base_name}"\n{channels}'),
        Column(
            Button(Const('Добавить канал'), id='get_channel_switcher', on_click=getters.check_account),
            SwitchTo(Const('Удалить канал'), id='del_channel', state=startSG.del_channel)
        ),
        SwitchTo(Const('⬅️Назад'), id='back_base', state=startSG.base),
        getter=getters.channels_getter,
        state=startSG.channels
    ),
    Window(
        Const('Отправьте ссылку|@username|Telegram ID канала или перешлите любое сообщение из него, '
              'к этому каналу прикрепится база'),
        TextInput(
            id='get_channel_link',
            on_success=getters.get_base_channel
        ),
        MessageInput(
            func=getters.get_forward_message,
            content_types=ContentType.ANY
        ),
        SwitchTo(Const('⬅️Назад'), id='back_channels', state=startSG.channels),
        state=startSG.get_base_channel
    ),
    Window(
        Const('Выберите канал, который вы хотели бы удалить'),
        Group(
            Select(
                Format('{item[0]}'),
                id='del_channel_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.del_channel_selector
            ),
            width=1
        ),
        SwitchTo(Const('⬅️Назад'), id='back_channels', state=startSG.channels),
        getter=getters.del_channel_getter,
        state=startSG.del_channel
    ),
    Window(
        Format('Вы подтверждаете удаление канала <em>"{title}"</em>?'),
        Column(
            Button(Const('🗑Удалить'), id='confirm_channel_del', on_click=getters.del_channel),
            SwitchTo(Const('❌Отмена'), id='back_channels', state=startSG.channels),
        ),
        getter=getters.del_channel_confirm_getter,
        state=startSG.del_channel_confirm
    ),
    Window(
        Format('<b>Меню привязки аккаунтов к базе "{base_name}"</b>\n\n{text}'),
        Column(
            SwitchTo(Const('➕Добавить аккаунт'), id='add_account', state=startSG.get_name),
            SwitchTo(Const('🗑Удалить аккаунт'), id='del_account_switcher', state=startSG.del_account)
        ),
        SwitchTo(Const('⬅️Назад'), id='back_base', state=startSG.base),
        getter=getters.accounts_getter,
        state=startSG.accounts
    ),
    Window(
        Const('Нажмите на аккаунт, вы хотели бы удалить👇'),
        Group(
            Select(
                Format("{item[0]}"),
                id='del_account_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.del_account_selector
            ),
            width=1
        ),
        Back(Const('⬅️Назад'), id='back_accounts'),
        getter=getters.del_account_getter,
        state=startSG.del_account
    ),
    Window(
        Format('Вы подтверждаете удаление аккаунта <em>"{name}"</em>?'),
        Column(
            Button(Const('🗑Удалить'), id='confirm_account_del', on_click=getters.del_account),
            SwitchTo(Const('❌Отмена'), id='back_accounts', state=startSG.accounts),
        ),
        getter=getters.del_account_confirm_getter,
        state=startSG.del_account_confirm
    ),
    Window(
        Const('Введите название для аккаунта'),
        TextInput(
            id='get_name',
            on_success=getters.get_name
        ),
        SwitchTo(Const('⬅️Назад'), id='back_accounts', state=startSG.accounts),
        state=startSG.get_name
    ),
    Window(
        Const('Выберите тип аккаунта'),
        Column(
            Button(Const('Депутатский'), id='special_type_choose', on_click=getters.choose_account_type),
            Button(Const('Обывательский'), id='general_type_choose', on_click=getters.choose_account_type),
        ),
        Back(Const('⬅️Назад'), id='back_get_name'),
        state=startSG.choose_account_type
    ),
    Window(
        Const('Отправьте номер телефона'),
        TextInput(
            id='get_phone',
            on_success=getters.phone_get,
        ),
        Back(Const('⬅️Назад'), id='back_choose_account_type'),
        SwitchTo(Const('Отмена'), id='back_accounts', state=startSG.accounts),
        state=startSG.add_account
    ),
    Window(
        Const('Введи код который пришел на ваш аккаунт в телеграмм в формате: 1-2-3-5-6'),
        TextInput(
            id='get_kod',
            on_success=getters.get_kod,
        ),
        state=startSG.kod_send
    ),
    Window(
        Const('Пароль от аккаунта телеграмм'),
        TextInput(
            id='get_password',
            on_success=getters.get_password,
        ),
        state=startSG.get_password
    ),
)