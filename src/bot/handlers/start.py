from aiogram import Router, types, F
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.bot.ui.templates import Templates
from src.bot.keyboards.inline import Keyboards
from src.database.models import User, Order, OrderStatus
from src.database.db import async_session

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    async with async_session() as session:
        # Register user if not exists
        user = await session.get(User, message.from_user.id)
        if not user:
            user = User(
                id=message.from_user.id,
                username=message.from_user.username,
                full_name=message.from_user.full_name
            )
            session.add(user)
            await session.commit()
    
    await message.answer(
        Templates.welcome(message.from_user.first_name),
        reply_markup=Keyboards.main_menu()
    )

@router.callback_query(lambda c: c.data == "support")
async def process_support(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer(
        f"{Templates.BRAND_HEADER}\n"
        "🆘 <b>Support</b>\n\n"
        "If you have any questions or need assistance with your order, "
        "please contact our support team:\n\n"
        "👤 @TokFlareSupport\n"
        "📧 support@tokflare.com"
    )

@router.callback_query(F.data == "profile")
async def process_profile(callback: types.CallbackQuery):
    await callback.answer()
    
    async with async_session() as session:
        # Count total orders
        stmt = select(Order).where(Order.user_id == callback.from_user.id)
        result = await session.execute(stmt)
        orders = result.scalars().all()
        total_spent = sum(o.total_price for o in orders if o.status == OrderStatus.COMPLETED)
        
    await callback.message.answer(
        f"{Templates.BRAND_HEADER}\n"
        f"👤 <b>Account Profile</b>\n\n"
        f"<b>Name:</b> {callback.from_user.full_name}\n"
        f"<b>ID:</b> <code>{callback.from_user.id}</code>\n\n"
        f"📊 <b>Stats:</b>\n"
        f"• Total Orders: {len(orders)}\n"
        f"• Total Spent: ${total_spent:.2f}\n\n"
        f"{Templates.SEPARATOR}\n"
        "<i>Thank you for using TokFlare!</i>"
    )
