from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
# Импорты клавиатур
from utils.keyboard import main_menu_keyboard, cancel_keyboard, LinkAccountCallback

# Импорты для работы с БД
from db.repository import get_user_by_verification_code, update_user_telegram_link

# Импорты для работы с FSM
from utils.states import LinkAccountStates

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "<b>Привет! Я бот для работы со смарт-контрактами.</b>\n"
        "Выберите действие:", reply_markup=main_menu_keyboard()
    )

# Обработчик нажатия кнопки "Привязать аккаунт"
@router.callback_query(F.data == LinkAccountCallback.LINK, StateFilter(None))
async def process_link_account_callback(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer(
        "Пожалуйста, введите 6-значный код подтверждения, полученный на сайте.",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(LinkAccountStates.waiting_for_code)
    await callback_query.answer()

# Обработчик ввода кода в состоянии waiting_for_code
@router.message(LinkAccountStates.waiting_for_code, F.text)
async def process_code_input(message: Message, state: FSMContext):
    code = message.text.strip()
    if len(code) == 6 and code.isalnum():
        await process_verification_code(message, code, state)
    else:
        await message.answer(
            "❌ Неверный формат кода. Код должен состоять из 6 символов.\\n"
            "Пожалуйста, введите корректный код или нажмите \"Отмена\".",
            reply_markup=cancel_keyboard()
        )

# Обработчик нажатия кнопки "Отмена" в любом состоянии
@router.callback_query(F.data == LinkAccountCallback.CANCEL, StateFilter("*"))
async def process_cancel_callback(callback_query: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await callback_query.answer("Нет активного действия для отмены.")
        return

    await state.clear()
    await callback_query.message.answer(
        "Действие отменено.",
        reply_markup=main_menu_keyboard()
    )
    await callback_query.answer()

async def process_verification_code(message: Message, code: str, state: FSMContext):
    chat_id = message.chat.id
    user = await get_user_by_verification_code(code)

    if user:
        updated = await update_user_telegram_link(telegram_user_id=chat_id, user_id=user['id'])
        if updated:
            await message.answer(
                "✅ Ваш Telegram аккаунт успешно привязан!",
                reply_markup=main_menu_keyboard()
            )
            await state.clear()
        else:
            await message.answer(
                "⚠️ Произошла ошибка при привязке аккаунта. Попробуйте позже или обратитесь в поддержку.",
                reply_markup=cancel_keyboard()
            )
    else:
        await message.answer(
            "❌ Неверный или устаревший код подтверждения.\\n"
            "Попробуйте запросить код снова на сайте или нажмите \"Отмена\".",
            reply_markup=cancel_keyboard()
        )
