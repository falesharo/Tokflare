from aiogram import Router, types, F
from aiogram.filters import Command
from sqlalchemy import select, func
from src.database.db import async_session
from src.database.models import Order, User, OrderStatus
from src.core.config import settings

router = Router()

def is_admin(user_id: int):
    return user_id in settings.ADMIN_IDS

@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    async with async_session() as session:
        # User count
        user_count_stmt = select(func.count(User.id))
        user_count = (await session.execute(user_count_stmt)).scalar()
        
        # Order stats
        total_orders_stmt = select(func.count(Order.id))
        total_orders = (await session.execute(total_orders_stmt)).scalar()
        
        completed_orders_stmt = select(func.count(Order.id)).where(Order.status == OrderStatus.COMPLETED)
        completed_orders = (await session.execute(completed_orders_stmt)).scalar()
        
        total_revenue_stmt = select(func.sum(Order.total_price)).where(Order.status == OrderStatus.COMPLETED)
        total_revenue = (await session.execute(total_revenue_stmt)).scalar() or 0.0

    await message.answer(
        "🛠 <b>TokFlare Admin Panel</b>\n\n"
        f"👥 <b>Total Users:</b> {user_count}\n"
        f"📦 <b>Total Orders:</b> {total_orders}\n"
        f"✅ <b>Completed Orders:</b> {completed_orders}\n"
        f"💰 <b>Total Revenue:</b> ${total_revenue:.2f}\n\n"
        "<i>Use /orders to see recent orders (not implemented)</i>"
    )
