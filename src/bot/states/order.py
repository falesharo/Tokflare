from aiogram.fsm.state import State, StatesGroup

class OrderStates(StatesGroup):
    waiting_for_link = State()
    waiting_for_drip_feed = State()
    waiting_for_runs = State()
    waiting_for_interval = State()
    waiting_for_quantity = State()
    waiting_for_comments = State()
    confirm_order = State()

class WalletStates(StatesGroup):
    waiting_for_amount = State()

class AdminStates(StatesGroup):
    waiting_for_margin = State()
    waiting_for_rate_limit = State()
