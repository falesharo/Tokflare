import re
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from src.bot.ui.templates import Templates
from src.bot.keyboards.inline import Keyboards
from src.bot.states.order import OrderStates
from src.bot.utils import generate_payment_qr
from src.core.config import settings
from src.core.services import OrderService
from src.core.smm.router import smm_router
from src.database.models import Order, OrderStatus
from src.database.db import async_session

router = Router()

TIKTOK_URL_PATTERN = re.compile(r'(https?://)?(www\.)?tiktok\.com/.+')

@router.callback_query(F.data == "order_new")
async def start_order_flow(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(OrderStates.waiting_for_link)
    await callback.message.edit_text(
        Templates.order_link(),
        reply_markup=Keyboards.cancel_order()
    )

@router.message(OrderStates.waiting_for_link)
async def process_link(message: types.Message, state: FSMContext):
    if not OrderService.validate_tiktok_url(message.text):
        await message.answer("❌ <b>Invalid Link</b>\nPlease send a valid TikTok video URL.")
        return
    
    processing_msg = await message.answer("⚙️ <b>Processing Link...</b>")
    await state.update_data(tiktok_url=message.text)
    await state.set_state(OrderStates.waiting_for_comments)
    
    await processing_msg.edit_text(
        Templates.order_comments(5, settings.MAX_COMMENTS),
        reply_markup=Keyboards.cancel_order()
    )

@router.message(OrderStates.waiting_for_comments)
async def process_comments(message: types.Message, state: FSMContext):
    comments = OrderService.parse_comments(message.text)
    is_valid, error_msg = OrderService.validate_comments(comments)
    
    if not is_valid:
        await message.answer(error_msg)
        return
    
    processing_msg = await message.answer("⚙️ <b>Calculating Total...</b>")
    count = len(comments)
    price, provider_cost = await OrderService.calculate_price(count)
    
    data = await state.get_data()
    await state.update_data(
        comments='\n'.join(comments), 
        comment_count=count, 
        total_price=price,
        provider_cost=provider_cost
    )
    
    await state.set_state(OrderStates.confirm_order)
    await processing_msg.edit_text(
        Templates.order_summary(data['tiktok_url'], count, price),
        reply_markup=Keyboards.confirm_order()
    )

@router.callback_query(F.data == "order_confirm")
async def confirm_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(OrderStates.selecting_payment)
    await callback.message.edit_text(
        Templates.payment_selection(),
        reply_markup=Keyboards.payment_methods()
    )

@router.callback_query(F.data == "order_cancel")
async def cancel_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Order cancelled.")
    await state.clear()
    await callback.message.edit_text(
        Templates.welcome(callback.from_user.first_name),
        reply_markup=Keyboards.main_menu()
    )

@router.callback_query(OrderStates.selecting_payment, F.data.startswith("pay_"))
async def process_payment_selection(callback: types.CallbackQuery, state: FSMContext):
    currency = callback.data.split("_")[1].upper()
    await callback.answer(f"Selected {currency}")
    
    data = await state.get_data()
    
    # In a real app, you would call NOWPayments API here to get an address
    # For now, we'll use a mock address
    mock_address = "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
    crypto_amount = data['total_price'] / 65000.0 if currency == "BTC" else data['total_price'] / 3500.0
    
    async with async_session() as session:
        new_order = Order(
            user_id=callback.from_user.id,
            tiktok_url=data['tiktok_url'],
            comments=data['comments'],
            comment_count=data['comment_count'],
            total_price=data['total_price'],
            provider_name=smm_router.active_provider_name,
            provider_cost=data.get('provider_cost'),
            status=OrderStatus.AWAITING_PAYMENT
        )
        session.add(new_order)
        await session.commit()
        await session.refresh(new_order)
        order_id = new_order.id

    await state.update_data(order_id=order_id)
    await state.set_state(OrderStates.awaiting_payment)
    
    # Generate QR Code
    qr_code = generate_payment_qr(mock_address, crypto_amount, currency)
    qr_file = types.BufferedInputFile(qr_code.read(), filename=f"payment_{order_id}.png")
    
    await callback.message.answer_photo(
        photo=qr_file,
        caption=Templates.payment_details(round(crypto_amount, 6), currency, mock_address),
        reply_markup=Keyboards.order_tracking(order_id)
    )
    # Delete the previous selection message
    await callback.message.delete()
