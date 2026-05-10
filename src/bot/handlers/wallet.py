from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from src.bot.ui.templates import Templates
from src.bot.ui.i18n import I18n
from src.bot.keyboards.inline import Keyboards
from src.core.services.credits import CreditService
from src.core.payments.nowpayments import NOWPayments
from src.database.models import Transaction, TransactionType, User
from src.database.db import async_session
from src.core.config import settings
from src.bot.states.order import WalletStates
from sqlalchemy import select
import logging
import uuid

router = Router()
logger = logging.getLogger(__name__)

async def update_app_screen(message: types.Message, text: str, reply_markup=None):
    try:
        await message.edit_text(text=text, reply_markup=reply_markup)
    except Exception:
        await message.answer(text=text, reply_markup=reply_markup)

@router.callback_query(F.data == "wallet")
async def show_wallet(callback: types.CallbackQuery, state: FSMContext, user: User):
    await callback.answer()
    await state.clear()
    
    lang = user.language
    async with async_session() as session:
        # Fetch fresh data
        db_user = await session.get(User, user.id)
        balance = db_user.balance
        tier = db_user.tier
        total_spent = db_user.total_spent
    
        stmt = select(Transaction).where(Transaction.user_id == user.id).order_by(Transaction.created_at.desc()).limit(3)
        result = await session.execute(stmt)
        transactions = result.scalars().all()
    
    transactions_text = "\n".join([
        f"• {t.type.value.replace('_', ' ').upper()}: ${t.amount_usd:.2f} <code>{t.created_at.strftime('%m/%d')}</code>"
        for t in transactions
    ]) if transactions else I18n.t("no_history", lang)
    
    text = Templates.wallet_dashboard(balance, tier, total_spent, lang)
    text += f"{I18n.t('activity_log', lang)}\n{transactions_text}"
    
    await update_app_screen(callback.message, text, Keyboards.wallet_menu(lang))

@router.callback_query(F.data == "deposit")
async def process_deposit(callback: types.CallbackQuery, state: FSMContext, user: User):
    await callback.answer()
    lang = user.language
    await update_app_screen(
        callback.message,
        I18n.t("deposit_system", lang),
        reply_markup=Keyboards.back_to_wallet(lang)
    )
    await state.set_state(WalletStates.waiting_for_amount)

@router.message(WalletStates.waiting_for_amount, F.text.regexp(r'^\d+(\.\d{1,2})?$'))
async def handle_deposit_amount(message: types.Message, state: FSMContext, user: User):
    try: await message.delete()
    except Exception: pass

    lang = user.language
    amount = float(message.text)
    if amount < 5: return

    await state.update_data(deposit_amount=amount)
    
    await message.answer(
        I18n.t("allocation", lang, amount=amount),
        reply_markup=Keyboards.payment_methods(back_callback="deposit", lang=lang)
    )

@router.callback_query(F.data.startswith("pay_"))
async def process_payment_selection(callback: types.CallbackQuery, state: FSMContext, user: User):
    await callback.answer("Initializing...")
    data = await state.get_data()
    amount = data.get('deposit_amount')
    lang = user.language
    
    if not amount:
        await callback.message.edit_text(I18n.t("session_timeout", lang), reply_markup=Keyboards.back_to_wallet(lang))
        return

    currency = callback.data.split("_")[1].upper()
    nowpayments = NOWPayments()
    external_id = str(uuid.uuid4())
    
    payment = await nowpayments.create_payment(amount, currency, external_id)
    
    if "error" in payment:
        await callback.message.edit_text(I18n.t("gateway_error", lang, error=payment['error']), reply_markup=Keyboards.back_to_wallet(lang))
        return

    async with async_session() as session:
        new_tx = Transaction(
            user_id=user.id,
            type=TransactionType.DEPOSIT,
            payment_id=payment['payment_id'],
            amount_usd=amount,
            amount_crypto=payment['pay_amount'],
            currency=currency,
            status="waiting",
            address=payment['pay_address']
        )
        session.add(new_tx)
        await session.commit()

    from src.bot.utils import generate_payment_qr
    qr_code = generate_payment_qr(payment['pay_address'], payment['pay_amount'], currency)
    qr_file = types.BufferedInputFile(qr_code.read(), filename=f"pay_{new_tx.payment_id}.png")

    await callback.message.answer_photo(
        photo=qr_file,
        caption=I18n.t("payment_waiting", lang, amount=payment['pay_amount'], currency=currency, address=payment['pay_address']),
        reply_markup=Keyboards.back_to_wallet(lang)
    )
    await callback.message.delete()
    await state.clear()
