from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func
from src.database.db import async_session
from src.database.models import Order, User, OrderStatus, Transaction, TransactionType
from src.core.config import settings
from src.bot.keyboards.inline import Keyboards
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

# Global Mock Settings (In production, these would be in DB)
ADMIN_SETTINGS = {
    "test_mode": False,
    "profit_margin": settings.PROFIT_MARGIN
}

class AdminStates(StatesGroup):
    waiting_for_margin = State()
    waiting_for_rate_limit = State()

def is_admin(user_id: int):
    return user_id in settings.ADMIN_IDS

@router.message(Command("admin"))
async def admin_panel_v2(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    async with async_session() as session:
        user_count = (await session.execute(select(func.count(User.id)))).scalar()
        total_orders = (await session.execute(select(func.count(Order.id)))).scalar()
        total_revenue = (await session.execute(select(func.sum(Order.total_price)).where(Order.status == OrderStatus.COMPLETED))).scalar() or 0.0
        total_deposits = (await session.execute(select(func.sum(Transaction.amount_usd)).where(Transaction.type == TransactionType.DEPOSIT))).scalar() or 0.0

    builder = InlineKeyboardBuilder()
    test_mode_text = "🟢 Test Mode: ON" if ADMIN_SETTINGS["test_mode"] else "🔴 Test Mode: OFF"
    builder.row(types.InlineKeyboardButton(text=test_mode_text, callback_data="admin_toggle_test"))
    builder.row(types.InlineKeyboardButton(text=f"📈 Margin: {ADMIN_SETTINGS['profit_margin']}x", callback_data="admin_set_margin"))
    builder.row(types.InlineKeyboardButton(text="👥 Manage Users", callback_data="admin_users"))
    builder.row(types.InlineKeyboardButton(text="🎟 Support Tickets", callback_data="admin_tickets"))
    builder.row(types.InlineKeyboardButton(text="🔄 Sync Services", callback_data="admin_sync"))
    builder.row(types.InlineKeyboardButton(text="📊 View Service Stats", callback_data="admin_service_stats"))
    builder.row(types.InlineKeyboardButton(text="🔧 Configure Settings", callback_data="admin_configure"))
    builder.row(types.InlineKeyboardButton(text="🛡️ Security Settings", callback_data="admin_security"))

    await message.answer(
        "🛠 <b>TokFlare SaaS Admin Dashboard</b>\n\n"
        f"👥 <b>Total Users:</b> {user_count}\n"
        f"📦 <b>Total Orders:</b> {total_orders}\n"
        f"💰 <b>Total Deposits:</b> ${total_deposits:.2f}\n"
        f"✨ <b>Net Revenue:</b> ${total_revenue:.2f}\n\n"
        "<i>Select an option to manage the platform:</i>",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "admin_toggle_test")
async def toggle_test_mode(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    ADMIN_SETTINGS["test_mode"] = not ADMIN_SETTINGS["test_mode"]
    await callback.answer(f"Test Mode {'Enabled' if ADMIN_SETTINGS['test_mode'] else 'Disabled'}")
    await admin_panel_v2(callback.message)
    await callback.message.delete()

@router.callback_query(F.data == "admin_sync")
async def admin_sync_services(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await callback.answer("🔄 Syncing services...")
    from src.core.smm.cache import service_cache
    await service_cache.refresh_cache()
    await callback.answer("✅ Services Synced!", show_alert=True)

@router.callback_query(F.data == "admin_service_stats")
async def admin_service_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await callback.answer("📊 Fetching service statistics...")
    from src.core.smm.cache import service_cache
    
    platforms = service_cache.get_platforms()
    stats_text = f"📊 <b>Service Statistics</b>\n\n"
    stats_text += f"🌐 <b>Platforms:</b> {len(platforms)}\n\n"
    
    for platform in platforms:
        actions = service_cache.get_actions(platform)
        stats_text += f"📂 <b>{platform}</b>\n"
        stats_text += f"   Actions: {len(actions)}\n"
        
        for action in actions:
            services = service_cache.get_services(platform, action)
            stats_text += f"   - {action}: {len(services)} services\n"
    
    await callback.message.answer(stats_text)

@router.callback_query(F.data == "admin_configure")
async def admin_configure(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await callback.answer("🔧 Opening configuration panel...")
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📈 Set Profit Margin", callback_data="admin_set_margin"))
    builder.row(types.InlineKeyboardButton(text="🔄 Back to Admin Panel", callback_data="admin"))
    
    await callback.message.answer(
        "🔧 <b>Configuration Panel</b>\n\n"
        "Select an option to configure:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "admin_security")
async def admin_security(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await callback.answer("🛡️ Opening security settings...")
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text=f"🔒 Rate Limit: {settings.RATE_LIMIT}/min", callback_data="admin_set_rate_limit"))
    builder.row(types.InlineKeyboardButton(text="🔄 Back to Admin Panel", callback_data="admin"))
    
    await callback.message.answer(
        "🛡️ <b>Security Settings</b>\n\n"
        f"Current Rate Limit: {settings.RATE_LIMIT} requests per minute\n"
        "Select an option to modify:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "admin_set_rate_limit")
async def admin_set_rate_limit(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await callback.answer()
    await callback.message.answer("Please enter the new rate limit (requests per minute):")
    
    await state.set_state(AdminStates.waiting_for_rate_limit)

@router.message(AdminStates.waiting_for_rate_limit)
async def handle_rate_limit_input(message: types.Message, state: FSMContext):
    try:
        rate_limit = int(message.text)
        if rate_limit <= 0:
            await message.answer("❌ Rate limit must be greater than 0.")
            return
        
        global settings
        settings.RATE_LIMIT = rate_limit
        
        await message.answer(f"✅ Rate limit updated to {rate_limit} requests per minute")
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Invalid input. Please enter a valid integer.")

@router.callback_query(F.data == "admin_set_margin")
async def admin_set_margin(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await callback.answer()
    await callback.message.answer("Please enter the new profit margin (e.g., 1.5 for 50%):")
    
    await state.set_state(AdminStates.waiting_for_margin)

@router.message(AdminStates.waiting_for_margin)
async def handle_margin_input(message: types.Message, state: FSMContext):
    try:
        margin = float(message.text)
        if margin <= 0:
            await message.answer("❌ Margin must be greater than 0.")
            return
        
        global ADMIN_SETTINGS
        ADMIN_SETTINGS["profit_margin"] = margin
        settings.PROFIT_MARGIN = margin
        
        await message.answer(f"✅ Profit margin updated to {margin}x")
        await state.clear()
        
        # Refresh service cache to apply new margin
        from src.core.smm.cache import service_cache
        await service_cache.refresh_cache()
        
    except ValueError:
        await message.answer("❌ Invalid input. Please enter a valid number.")
