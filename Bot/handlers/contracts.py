import asyncio
from aiogram import Router, F, types, Bot
from aiogram.types import Message, CallbackQuery, InputFile, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from utils.states import AddContractState, DeleteContractState
from utils.keyboard import main_menu_keyboard
import db.repository as repository
import services.audit as audit
import services.visualization as visualization
from services.get_contract_name import get_contract_name, ContractVerificationError, NetworkAccessError
import logging

router = Router()

SUPPORTED_NETWORKS = {
    "mainnet": "ETH Mainnet",
    "base": "Base",
    "arbitrum": "Arbitrum"
}

def create_network_keyboard():
    buttons = [
        [types.InlineKeyboardButton(text=name, callback_data=f"net_{net_id}")]
        for net_id, name in SUPPORTED_NETWORKS.items()
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def create_source_keyboard():
    buttons = [
        [types.InlineKeyboardButton(text="Выбрать из отслеживаемых", callback_data="select_tracked")],
        [types.InlineKeyboardButton(text="Другой контракт", callback_data="select_other")],
        [types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

@router.callback_query(F.data == "add_contract")
async def menu_add_contract(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(action="add")
    await callback.message.answer("Выберите сеть:", reply_markup=create_network_keyboard())
    await state.set_state(AddContractState.selecting_network)
    await callback.answer()

@router.callback_query(F.data == "audit_contract")
async def menu_audit_contract(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(action="audit")
    await callback.message.answer("Выберите источник контракта для аудита:", reply_markup=create_source_keyboard())
    await state.set_state(AddContractState.choosing_source)
    await callback.answer()

@router.callback_query(F.data == "visualize_contract")
async def menu_visualize_contract(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(action="visualize")
    await callback.message.answer("Выберите источник контракта для визуализации:", reply_markup=create_source_keyboard())
    await state.set_state(AddContractState.choosing_source)
    await callback.answer()


# --- Обработка выбора источника контракта --- #
@router.callback_query(AddContractState.choosing_source, F.data == "select_tracked")
async def process_source_tracked(callback: types.CallbackQuery, state: FSMContext):
    user_id = int(callback.from_user.id)
    contracts = await repository.get_user_contracts(user_id)

    if not contracts:
        await callback.message.edit_text("📄 У вас пока нет отслеживаемых контрактов. Сначала добавьте контракт.")
        await state.clear()
        await callback.message.answer("🏠 Главное меню:", reply_markup=main_menu_keyboard())
        await callback.answer()
        return

    response = "📄 Ваши отслеживаемые контракты:\n\n"
    contract_dict = {}
    for i, (network, address, contract_name) in enumerate(contracts, 1):
        network_name = SUPPORTED_NETWORKS.get(network, network)
        name_display = f" ({contract_name})" if contract_name and contract_name != "noname" else ""
        response += f"{i}. 🌐 Сеть: {network_name}\n"
        response += f"   🏷️ Имя:{name_display}\n"
        response += f"   <code>{address}</code>\n\n"
        contract_dict[str(i)] = {"network": network, "address": address, "name": contract_name}

    response += "\n🔢 Введите номер контракта:"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
    ])

    await callback.message.edit_text(response, reply_markup=kb, parse_mode="HTML")
    await state.update_data(tracked_contracts=contract_dict)
    await state.set_state(AddContractState.selecting_tracked)
    await callback.answer()

# --- Обработка выбора ввода "другого контракта" --- #
@router.callback_query(AddContractState.choosing_source, F.data == "select_other")
async def process_source_other(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите сеть:", reply_markup=create_network_keyboard())
    await state.set_state(AddContractState.selecting_network)
    await callback.answer()


# --- Обработка ввода номера отслеживаемого контракта --- #
@router.message(AddContractState.selecting_tracked)
async def process_tracked_contract_selection(message: types.Message, state: FSMContext):
    user_input = message.text.strip()
    data = await state.get_data()
    tracked_contracts = data.get('tracked_contracts', {})
    action = data.get("action")

    selected_contract = None
    if user_input.isdigit() and user_input in tracked_contracts:
        selected_contract = tracked_contracts[user_input]
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
        ])
        await message.answer(
            "⚠️ Неверный номер контракта. Попробуйте снова или отмените операцию.",
            reply_markup=kb
        )
        return

    if selected_contract:
        addr = selected_contract['address']
        network = selected_contract['network']
        contract_name = selected_contract.get('name')

        await state.update_data(addr=addr, network=network, contract_name=contract_name)

        confirmation_text = f"Выбрана сеть: <b>{SUPPORTED_NETWORKS.get(network, network)}</b>\n"
        confirmation_text += f"Выбран отслеживаемый адрес: <code>{addr}</code>\n"

        if contract_name == "noname" or not contract_name:
            confirmation_text += "Имя контракта <b>не задано</b>\n"
        else:
            confirmation_text += f"Имя контракта: <b>{contract_name}</b>\n"

        if action == "audit":
            confirm_button_text = "✅ Провести аудит выбранного контракта"
        elif action == "visualize":
            confirm_button_text = "✅ Визуализировать выбранный контракт"
        else:
            confirm_button_text = "✅ Подтвердить выбор"

        confirmation_text += f"\nПодтвердите действие."

        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=confirm_button_text, callback_data="confirm_addr")],
            [types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
        ])
        await message.answer(confirmation_text, reply_markup=kb, parse_mode="HTML")
        await state.set_state(AddContractState.confirming)

    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
        ])
        await message.answer(
            "⚠️ Произошла ошибка при выборе контракта. Попробуйте снова или отмените операцию.",
            reply_markup=kb
        )


# --- Обработка выбора сети --- #
@router.callback_query(AddContractState.selecting_network, F.data.startswith("net_"))
async def process_network_selection(callback: types.CallbackQuery, state: FSMContext):
    network_id = callback.data.split("_")[1]
    if network_id not in SUPPORTED_NETWORKS:
        await callback.answer("Некорректная сеть", show_alert=True)
        return
    await state.update_data(network=network_id)
    await callback.message.edit_reply_markup(None)
    await callback.message.edit_text(f"Выбрана сеть: {SUPPORTED_NETWORKS[network_id]}.\nТеперь введите адрес контракта:")
    await state.set_state(AddContractState.entering_address)
    await callback.answer()


# --- Обработка ввода адреса ---
@router.message(AddContractState.entering_address)
async def process_address(message: types.Message, state: FSMContext):
    addr = message.text.strip()
    data = await state.get_data()
    network = data.get("network")
    action = data.get("action")

    cancel_kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
    ])

    try:
        await message.answer("🔍 Проверяю адрес контракта...")
        contract_name = await get_contract_name(addr, network)
        if contract_name is None:
            network_name = SUPPORTED_NETWORKS.get(network, network)
            await message.answer(
                f"⚠️ Не удалось найти контракт <code>{addr}</code> в сети {network_name}.\n"
                f"Пожалуйста, введите другой адрес или отмените операцию.",
                parse_mode="HTML",
                reply_markup=cancel_kb
            )
            return
        await state.update_data(addr=addr, contract_name=contract_name)

        confirmation_text = f"Выбрана сеть: <b>{SUPPORTED_NETWORKS.get(network, network)}</b>\n"
        confirmation_text += f"Введен адрес: <code>{addr}</code>\n"

        if contract_name == "noname":
            confirmation_text += "Контракт существует, но имя контракта <b>не задано</b>\n"
        else:
            confirmation_text += f"Имя контракта: <b>{contract_name}</b>\n"

        if action == "add":
            confirm_button_text = "✅ Добавить контракт в отслеживание"
        elif action == "audit":
            confirm_button_text = "✅ Провести аудит контракта"
        elif action == "visualize":
            confirm_button_text = "✅ Визуализировать контракт"
        else:
            confirm_button_text = "✅ Подтвердить"

        confirmation_text += f"\nПодтвердите действие."

        confirm_kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=confirm_button_text, callback_data="confirm_addr")],
            [types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
        ])
        await message.answer(confirmation_text, reply_markup=confirm_kb, parse_mode="HTML")
        await state.set_state(AddContractState.confirming)

    # Обработка ситуации, когда контракт найден, но есть проблема с верификацией
    except ContractVerificationError as e:
        network_name = SUPPORTED_NETWORKS.get(network, network)
        await message.answer(
            f"⚠️ Контракт <code>{addr}</code> в сети {network_name} найден, но есть проблема с верификацией:\n"
            f"<i>{e}</i>\n"
            f"Вы можете попробовать ввести другой адрес или отменить операцию.",
            parse_mode="HTML",
            reply_markup=cancel_kb
        )
        return

    # Обработка ситуации, когда возникла временная ошибка сети
    except NetworkAccessError as e:
        logging.warning(f"Network access error for {addr} on {network}: {e}")
        network_name = SUPPORTED_NETWORKS.get(network, network)
        await message.answer(
            f"🔌 Возникла временная проблема при доступе к сервису сети {network_name} для проверки адреса <code>{addr}</code>.\n"
            f"Операция отменена. Пожалуйста, попробуйте позже.",
            parse_mode="HTML"
        )
        await state.clear()
        await message.answer("🏠 Главное меню:", reply_markup=main_menu_keyboard())

    # Другие непредвиденные ошибки при получении имени
    except Exception as e:
        logging.error(f"Error getting contract name for {addr} on {network}: {e}")
        network_name = SUPPORTED_NETWORKS.get(network, network)
        await message.answer(
            f"⚠️ Не удалось получить информацию о контракте <code>{addr}</code> в сети {network_name} из-за технической ошибки.\n"
            f"Пожалуйста, введите другой адрес, попробуйте позже или отмените операцию.",
            parse_mode="HTML",
            reply_markup=cancel_kb
        )
        return


# --- Подтверждение выбора адреса --- #
@router.callback_query(AddContractState.confirming, F.data == "confirm_addr")
async def confirm_address(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    addr = data.get("addr")
    action = data.get("action")
    network = data.get("network")
    contract_name = data.get("contract_name")
    await callback.message.edit_reply_markup(None)
    user_id = int(callback.from_user.id)

    display_name = f" '{contract_name}'" if contract_name and contract_name != "noname" else ""
    network_name = SUPPORTED_NETWORKS.get(network, network)

    if action == "add":
        saved = await repository.save_contract(user_id, network, addr, contract_name)
        if saved:
            await callback.message.answer(f"💾 Контракт{display_name} <code>{addr}</code> в сети {network_name} сохранен.", parse_mode="HTML")
        else:
            await callback.message.answer(f"⚠️ Контракт <code>{addr}</code> в сети {network_name} уже отслеживается.", parse_mode="HTML")

    elif action == "audit":
        await callback.message.answer(f"🔎 Запускаю аудит смарт-контракта{display_name} <code>{addr}</code> в сети {network_name}, подождите...", parse_mode="HTML")
        try:
            pdf = await audit.audit_contract(addr, network)
            await callback.message.answer(f"✅ Аудит завершён:")
            pdf_input_file = BufferedInputFile(file=pdf, filename=f"audit_report_{addr}.pdf")
            await callback.message.answer_document(document=pdf_input_file)
        except Exception as e:
            logging.error(f"Audit failed for {addr} on {network}: {e}")
            await callback.message.answer(f"❌ Не удалось провести аудит контракта{display_name} <code>{addr}</code>.", parse_mode="HTML")

    elif action == "visualize":
        await callback.message.answer(f"⏳ Генерирую ссылку на визуализацию для контракта{display_name} <code>{addr}</code> в сети {network_name}...", parse_mode="HTML")
        try:
            graph_url = await visualization.get_contract_graph_url(addr, network)
            await callback.message.answer(f"""✅ Визуализация готова!

Граф контракта доступен по ссылке:
<code>{graph_url}</code>""", parse_mode="HTML")
        except ConnectionError as e:
            logging.warning(f"Visualization connection failed for {addr} on {network}: {e}")
            await callback.message.answer(f"🔌 Не удалось подключиться к сервису визуализации для контракта{display_name} <code>{addr}</code>. Попробуйте позже.", parse_mode="HTML")
        except TimeoutError as e:
            logging.warning(f"Visualization timeout for {addr} on {network}: {e}")
            await callback.message.answer(f"⏳ Сервис визуализации не ответил вовремя для контракта{display_name} <code>{addr}</code>. Попробуйте позже.", parse_mode="HTML")
        except ValueError as e:
            logging.error(f"Visualization data error for {addr} on {network}: {e}")
            await callback.message.answer(f"⚠️ Сервис визуализации вернул некорректные данные для контракта{display_name} <code>{addr}</code>.", parse_mode="HTML")
        except Exception as e:
            logging.error(f"Visualization failed for {addr} on {network}: {e}")
            await callback.message.answer(f"❌ Не удалось создать визуализацию для контракта{display_name} <code>{addr}</code> из-за непредвиденной ошибки.", parse_mode="HTML")

    await state.clear()
    await callback.message.answer("🏠 Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()

# --- Общий обработчик отмены для состояний AddContractState ---
@router.callback_query(StateFilter(AddContractState), F.data == "cancel_action")
async def cancel_add_contract_steps(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_text("❌ Операция отменена.")
    except Exception:
        await callback.message.answer("❌ Операция отменена.")

    await state.clear()
    await callback.message.answer("🏠 Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()


# --- Просмотр отслеживаемых контрактов --- #
@router.callback_query(F.data == "view_contracts")
async def view_tracked_contracts(callback: types.CallbackQuery):
    user_id = int(callback.from_user.id)

    # {network, address, contract_name}[]
    contracts = await repository.get_user_contracts(user_id)

    if not contracts:
        await callback.message.answer("📄 У вас пока нет отслеживаемых контрактов.")
    else:
        response = "📄 Ваши отслеживаемые контракты:\n\n"
        for i, (network, address, contract_name) in enumerate(contracts, 1):
            network_name = SUPPORTED_NETWORKS.get(network, network)
            name_display = f" ({contract_name})" if contract_name and contract_name != "noname" else ""
            response += f"{i}. 🌐 Сеть: {network_name}\n"
            response += f"   🏷️ Имя:{name_display}\n"
            response += f"   <code>{address}</code>\n\n"
        await callback.message.answer(response, parse_mode="HTML")

    await callback.message.answer("🏠 Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()


# --- Удаление контракта (1 этап) --- #
@router.callback_query(F.data == "delete_contract_start")
async def delete_contract_start(callback: types.CallbackQuery, state: FSMContext):
    user_id = int(callback.from_user.id)

    contracts = await repository.get_user_contracts(user_id)

    if not contracts:
        await callback.message.answer("🗑️ У вас нет контрактов для удаления.")
        await callback.message.answer("🏠 Главное меню:", reply_markup=main_menu_keyboard())
        await callback.answer()
        return

    response = "📄 Доступные для удаления контракты:\n\n"
    contract_dict = {}
    for i, (network, address, contract_name) in enumerate(contracts, 1):
        network_name = SUPPORTED_NETWORKS.get(network, network)
        name_display = f" ({contract_name})" if contract_name and contract_name != "noname" else ""
        response += f"{i}. 🌐 Сеть: {network_name}\n"
        response += f"   🏷️ Имя:{name_display}\n"
        response += f"   <code>{address}</code>\n\n"
        contract_dict[str(i)] = {"network": network, "address": address, "name": contract_name}

    response += "\n🔢 Введите номер контракта, который хотите удалить:"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
    ])

    await callback.message.answer(response, reply_markup=kb, parse_mode="HTML")
    await state.update_data(contracts_for_delete=contract_dict)
    await state.set_state(DeleteContractState.entering_address)
    await callback.answer()


# --- Удаление контракта (2 этап) --- #
@router.message(DeleteContractState.entering_address)
async def process_delete_address(message: types.Message, state: FSMContext):
    user_input = message.text.strip()
    user_id = int(message.from_user.id)
    data = await state.get_data()
    contracts_for_delete = data.get('contracts_for_delete', {})

    network_to_delete = None
    address_to_delete = None
    name_to_delete = None

    # Проверяем, ввел ли пользователь номер из словаря
    if user_input.isdigit() and user_input in contracts_for_delete:
        contract_info = contracts_for_delete[user_input]
        network_to_delete = contract_info['network']
        address_to_delete = contract_info['address']
        name_to_delete = contract_info.get('name')
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
        ])
        await message.answer(
            "⚠️ Неверный номер контракта. Попробуйте снова или отмените удаление.",
            reply_markup=kb
        )
        return

    if network_to_delete and address_to_delete:
        deleted = await repository.delete_contract(user_id, network_to_delete, address_to_delete)
        if deleted:
            network_name = SUPPORTED_NETWORKS.get(network_to_delete, network_to_delete)
            display_name = f" '{name_to_delete}'" if name_to_delete and name_to_delete != "noname" else ""
            await message.answer(f"🗑️ Контракт{display_name} <code>{address_to_delete}</code> в сети {network_name} удален из отслеживания.", parse_mode="HTML")
        else:
            await message.answer("⚠️ Не удалось удалить контракт. Возможно, он уже был удален.")

        await state.clear()
        await message.answer("🏠 Главное меню:", reply_markup=main_menu_keyboard())
    else:
        await message.answer("⚠️ Произошла ошибка при определении контракта для удаления. Попробуйте снова.")
        await state.clear()
        await message.answer("🏠 Главное меню:", reply_markup=main_menu_keyboard())
