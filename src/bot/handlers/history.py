from aiogram import Router, types, F
from sqlalchemy import select
from src.database.db import async_session
from src.database.models import Order, OrderStatus
from src.bot.ui.templates import Templates
from src.bot.keyboards.inline import Keyboards

router = Router()

@router.callback_query(F.data == "order_history")
async def show_history(callback: types.CallbackQuery):
    await callback.answer()
    
    async with async_session() as session:
        stmt = select(Order).where(Order.user_id == callback.from_user.id).order_by(Order.created_at.desc()).limit(5)
        result = await session.execute(stmt)
        orders = result.scalars().all()

    if not orders:
        await callback.message.edit_text(
            f"{Templates.BRAND_HEADER}\n"
            "📜 <b>Order History</b>\n\n"
            "You haven't placed any orders yet. Start your first order now! 🚀",
            reply_markup=Keyboards.back_to_main()
        )
        return

    history_text = f"{Templates.BRAND_HEADER}\n📜 <b>Recent Orders</b>\n\n"
    for order in orders:
        status_emoji = "⏳" if order.status == OrderStatus.AWAITING_PAYMENT else "✅" if order.status == OrderStatus.COMPLETED else "⚙️"
        service_name = order.service_id or 'N/A'
        
        # Try to get more detailed service info from cache
        if order.service_id:
            service = service_cache.get_service_details(order.service_id)
            service_name = service.get('display_name', order.service_id)
        
        history_text += (
            f"🆔 <b>Order #{order.id}</b>\n"
            f"📊 Status: {status_emoji} {order.status.value.capitalize()}\n"
            f"💰 Price: ${order.total_price:.2f}\n"
            f"📅 Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"🔗 <b>Service:</b> {service_name}\n"
            f"{Templates.SEPARATOR}\n"
        )

    await callback.message.edit_text(history_text, reply_markup=Keyboards.back_to_main())

@router.callback_query(F.data.startswith("track_"))
async def refresh_tracking(callback: types.CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    
    async with async_session() as session:
        order = await session.get(Order, order_id)
        
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    status_emoji = "⏳" if order.status == OrderStatus.AWAITING_PAYMENT else "✅" if order.status == OrderStatus.COMPLETED else "⚙️"
    
    await callback.answer(f"Status: {order.status.value.capitalize()}")
    
    # Update the message if status changed
    text = (
        f"{Templates.BRAND_HEADER}\n"
        f"🆔 <b>Order #{order.id} Tracking</b>\n\n"
        f"📊 <b>Current Status:</b> {status_emoji} {order.status.value.upper()}\n"
        f"🔗 <b>Link:</b> {order.tiktok_url}\n"
        f"💬 <b>Comments:</b> {order.comment_count}\n\n"
        f"<i>Last updated: {order.created_at.strftime('%H:%M:%S')}</i>"
    )
    
    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=Keyboards.order_tracking(order_id)
        )
    else:
        await callback.message.edit_text(
            text=text,
            reply_markup=Keyboards.order_tracking(order_id)
        )
