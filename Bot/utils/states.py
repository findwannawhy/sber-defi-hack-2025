from aiogram.fsm.state import State, StatesGroup

class LinkAccountStates(StatesGroup):
    waiting_for_code = State()

class AddContractState(StatesGroup):
    choosing_source = State()
    selecting_network = State()
    entering_address = State()
    selecting_tracked = State()
    confirming = State()

class DeleteContractState(StatesGroup):
    entering_address = State()