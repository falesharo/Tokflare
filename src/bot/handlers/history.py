from aiogram import Router, types, F
from sqlalchemy import select
from src.database.db import async_session
from src.database.models import Order, OrderStatus, User
from src.bot.ui.templates import Templates
from src.bot.keyboards.inline import Keyboards
from src.bot.utils import update_app_screen
from src.core.config import settings
import logging

router = Router()

@router.callback_query(F.data == "order_history")
async def show_history(callback: types.CallbackQuery, user: User):
    await callback.answer()
    lang = user.language
    
    async with async_session() as session:
        stmt = select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc()).limit(10)
        result = await session.execute(stmt)
        orders = result.scalars().all()

    if not orders:
        text = (
            f"{Templates.BRAND_HEADER}\n"
            "📜 <b>ORDER HISTORY</b>\n\n"
            "No active deployments found in your records."
        )
        await update_app_screen(callback.message, text, Keyboards.back_to_main(lang), media_path=settings.LOGO_PATH)
        return

    history_text = f"{Templates.BRAND_HEADER}\n📜 <b>RECENT DEPLOYMENTS</b>\n\n"
    for order in orders:
        status_emoji = "⏳" if order.status == OrderStatus.AWAITING_PAYMENT else "✅" if order.status == OrderStatus.COMPLETED else "⚙️"
        history_text += (
            f"🆔 <b>#{order.id}</b> | {status_emoji} {order.status.value.upper()}\n"
            f"💰 Value: ${order.total_price:.2f}\n"
            f"📅 Date: {order.created_at.strftime('%Y-%m-%d')}\n"
            f"{Templates.SEPARATOR}\n"
        )

    await update_app_screen(callback.message, history_text, Keyboards.back_to_main(lang), media_path=settings.LOGO_PATH)

@router.callback_query(F.data.startswith("track_"))
async def refresh_tracking(callback: types.CallbackQuery, user: User):
    order_id = int(callback.data.split("_")[1])
    lang = user.language
    
    async with async_session() as session:
        order = await session.get(Order, order_id)
    
    if not order:
        await callback.answer("Order not found.")
        return

    status_emoji = "⏳" if order.status == OrderStatus.AWAITING_PAYMENT else "✅" if order.status == OrderStatus.COMPLETED else "⚙️"
    
    text = (
        f"{Templates.BRAND_HEADER}\n"
        f"🆔 <b>Order #{order.id} Tracking</b>\n\n"
        f"📊 <b>Current Status:</b> {status_emoji} {order.status.value.upper()}\n"
        f"🔗 <b>Link:</b> {order.tiktok_url}\n"
        f"💬 <b>Quantity:</b> {order.comment_count}\n\n"
        f"<i>Last updated: {order.created_at.strftime('%H:%M:%S')}</i>"
    )
    
    # We DON'T force the logo here, because if they are tracking from the QR code screen, 
    # we want to keep the QR code visible so they can pay.
    await update_app_screen(callback.message, text, Keyboards.order_tracking(order_id, lang))
