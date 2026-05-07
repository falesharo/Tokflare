from aiogram.fsm.state import State, StatesGroup

class OrderStates(StatesGroup):
    waiting_for_link = State()
    waiting_for_comments = State()
    confirm_order = State()
    selecting_payment = State()
    awaiting_payment = State()
