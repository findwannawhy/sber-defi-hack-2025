from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

class LinkAccountCallback:
    LINK = "link_account"
    CANCEL = "cancel_linking"

def main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Добавить контракт", callback_data="add_contract"))
    builder.row(InlineKeyboardButton(text="🔎 Аудит контракта", callback_data="audit_contract"))
    builder.row(InlineKeyboardButton(text="📈 Визуализировать контракт", callback_data="visualize_contract"))
    builder.row(InlineKeyboardButton(text="📄 Список добавленных контрактов", callback_data="view_contracts"))
    builder.row(InlineKeyboardButton(text="🗑️ Удалить контракт из отслеживания", callback_data="delete_contract_start"))
    builder.row(InlineKeyboardButton(text="🔗 Привязать аккаунт", callback_data=LinkAccountCallback.LINK))
    return builder.as_markup()

def cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data=LinkAccountCallback.CANCEL))
    return builder.as_markup()