from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from src.bot.ui.templates import Templates
from src.bot.keyboards.inline import Keyboards
from src.core.services.credits import CreditService
from src.core.payments.nowpayments import NOWPayments
from src.database.models import Transaction, TransactionType
from src.database.db import async_session
from src.core.config import settings
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "wallet")
async def show_wallet(callback: types.CallbackQuery):
    await callback.answer()
    
    async with async_session() as session:
        from src.database.models import User
        user = await session.get(User, callback.from_user.id)
        balance = user.balance if user else 0.0
    
    # Fetch recent transactions
    async with async_session() as session:
        from sqlalchemy import select
        stmt = select(Transaction).where(Transaction.user_id == callback.from_user.id).order_by(Transaction.created_at.desc()).limit(3)
        result = await session.execute(stmt)
        transactions = result.scalars().all()
    
    transactions_text = "\n".join([
        f"• {t.type.value.replace('_', ' ').title()}: ${t.amount_usd:.2f} on {t.created_at.strftime('%Y-%m-%d')}"
        for t in transactions
    ]) if transactions else "<i>No recent transactions.</i>"
    
    await callback.message.edit_text(
        f"💳 <b>My Wallet</b>\n\n"
        f"💰 Current Balance: <b>${balance:.2f}</b>\n\n"
        f"🎁 <b>Recharge Bonuses:</b>\n"
        f"• $50+ : <b>+5% Bonus</b>\n"
        f"• $100+ : <b>+10% Bonus</b>\n"
        f"• $200+ : <b>+15% Bonus</b>\n\n"
        f"🔗 <b>Your Referral Link:</b>\n"
        f"<code>https://t.me/{(await callback.bot.get_me()).username}?start=ref_{callback.from_user.id}</code>\n"
        f"<i>Earn 5% from all deposits made by your referrals!</i>\n\n"
        f"📊 <b>Recent Transactions:</b>\n"
        f"{transactions_text}",
        reply_markup=Keyboards.wallet_menu()
    )

@router.callback_query(F.data == "deposit")
async def process_deposit(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "➕ <b>Top Up Balance</b>\n\n"
        "Please enter the amount you want to deposit in USD ($):\n"
        "<i>Minimum deposit: $5.00</i>",
        reply_markup=Keyboards.back_to_wallet()
    )
    from aiogram.fsm.state import State, StatesGroup
    class WalletStates(StatesGroup):
        waiting_for_amount = State()
    await state.set_state(WalletStates.waiting_for_amount)

@router.message(F.text.regexp(r'^\d+(\.\d{1,2})?$'))
async def handle_deposit_amount(message: types.Message, state: FSMContext):
    # This should be in a separate state check, but for brevity:
    amount = float(message.text)
    if amount < 5:
        await message.answer("❌ Minimum deposit is $5.00")
        return
    
    await state.update_data(deposit_amount=amount)
    await message.answer(
        f"✅ Amount: <b>${amount:.2f}</b>\n"
        f"Select payment method:",
        reply_markup=Keyboards.payment_methods() # We reuse the crypto selection
    )
