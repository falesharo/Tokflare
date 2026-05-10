from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from src.bot.ui.templates import Templates
from src.bot.ui.i18n import I18n
from src.bot.keyboards.inline import Keyboards
from src.core.smm.cache import service_cache
from src.core.smm.catalog import CatalogManager
from src.core.services.order_service import OrderService
from src.core.services.credits import CreditService
from src.core.smm.router import smm_router
from src.database.db import async_session
from src.database.models import Order, OrderStatus, User, TransactionType
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.bot.states.order import OrderStates
import logging

router = Router()
logger = logging.getLogger(__name__)

# --- HELPERS ---
async def cleanup_user_input(message: types.Message):
    """Deletes the user's message to keep the chat clean."""
    try: await message.delete()
    except Exception: pass

async def update_app_screen(message: types.Message, text: str, reply_markup=None):
    """Edits the previous bot message to simulate an app screen."""
    try: await message.edit_text(text=text, reply_markup=reply_markup)
    except Exception: await message.answer(text=text, reply_markup=reply_markup)

# --- HANDLERS ---

@router.callback_query(F.data == "order_new")
async def start_order_v6(callback: types.CallbackQuery, state: FSMContext, user: User):
    await callback.answer()
    platforms = CatalogManager.get_platforms()
    await update_app_screen(callback.message, Templates.welcome(callback.from_user.first_name, user.tier, user.language), Keyboards.platforms(platforms, user.language))

@router.callback_query(F.data.startswith("plat_"))
async def select_platform(callback: types.CallbackQuery, state: FSMContext, user: User):
    await callback.answer()
    platform = callback.data.split("_")[1]
    await state.update_data(platform=platform)
    actions = CatalogManager.get_actions(platform)
    
    builder = InlineKeyboardBuilder()
    for act in actions:
        builder.row(types.InlineKeyboardButton(text=act, callback_data=f"act_{act[:10]}"))
    builder.row(types.InlineKeyboardButton(text=I18n.t("btn_back", user.language), callback_data="order_new"))
    
    text = f"{Templates.BRAND_HEADER}\n" + I18n.t("network_select", user.language, platform=platform)
    await update_app_screen(callback.message, text, builder.as_markup())

@router.callback_query(F.data.startswith("act_"))
async def select_category(callback: types.CallbackQuery, state: FSMContext, user: User):
    await callback.answer()
    action_prefix = callback.data.split("_")[1]
    data = await state.get_data()
    platform = data.get('platform')
    
    actions = CatalogManager.get_actions(platform)
    full_action = next((a for a in actions if a.startswith(action_prefix)), "Other")
    products = CatalogManager.get_products(platform, full_action)
    
    builder = InlineKeyboardBuilder()
    for p in products:
        # Multilingual product name
        prod_name = I18n.t(f"name_{p.id}", user.language)
        builder.row(types.InlineKeyboardButton(text=prod_name, callback_data=f"prod_{p.id}"))
    builder.row(types.InlineKeyboardButton(text=I18n.t("btn_back", user.language), callback_data=f"plat_{platform}"))
    
    text = f"{Templates.BRAND_HEADER}\n" + I18n.t("quality_select", user.language, platform=platform, action=full_action)
    await update_app_screen(callback.message, text, builder.as_markup())

@router.callback_query(F.data.startswith("prod_"))
async def enter_link_step(callback: types.CallbackQuery, state: FSMContext, user: User):
    await callback.answer()
    product_id = callback.data[5:]
    product = CatalogManager.get_product_by_id(product_id)
    if not product: return

    service_data = service_cache.get_service_details(product.smm_service_id)
    
    # Get localized name, description and hint
    prod_name = I18n.t(f"name_{product.id}", user.language)
    desc = I18n.t(f"desc_{product.id}", user.language)
    hint = I18n.t(f"hint_{product.link_hint}", user.language)
    
    await state.update_data(
        product_id=product_id,
        service_id=product.smm_service_id, 
        service_name=prod_name, 
        rate=service_data.get('user_price_per_1000', 0.0),
        min_qty=int(service_data.get('min', 10)),
        max_qty=int(service_data.get('max', 10000)),
        app_msg_id=callback.message.message_id
    )
    
    await update_app_screen(callback.message, Templates.order_link(prod_name, desc, hint, user.language), Keyboards.cancel_order(user.language))
    await state.set_state(OrderStates.waiting_for_link)

@router.message(OrderStates.waiting_for_link)
async def process_link_v3(message: types.Message, state: FSMContext, user: User):
    await cleanup_user_input(message)
    data = await state.get_data()
    
    if not OrderService.validate_url(message.text):
        await message.bot.edit_message_text(
            chat_id=message.chat.id, message_id=data['app_msg_id'],
            text=f"{Templates.BRAND_HEADER}\n" + I18n.t("entry_error", user.language),
            reply_markup=Keyboards.cancel_order(user.language)
        )
        return

    await state.update_data(target_url=message.text)
    
    if "Comment" in data['service_name']:
        await message.bot.edit_message_text(
            chat_id=message.chat.id, message_id=data['app_msg_id'],
            text=f"{Templates.BRAND_HEADER}\n" + I18n.t("input_required", user.language),
            reply_markup=Keyboards.cancel_order(user.language)
        )
        await state.set_state(OrderStates.waiting_for_comments)
    else:
        await message.bot.edit_message_text(
            chat_id=message.chat.id, message_id=data['app_msg_id'],
            text=Templates.order_quantity(data['min_qty'], data['max_qty'], user.language),
            reply_markup=Keyboards.cancel_order(user.language)
        )
        await state.set_state(OrderStates.waiting_for_quantity)

@router.message(OrderStates.waiting_for_quantity)
async def process_quantity(message: types.Message, state: FSMContext, user: User):
    await cleanup_user_input(message)
    data = await state.get_data()
    
    try:
        qty = int(message.text)
        if not (data['min_qty'] <= qty <= data['max_qty']): raise ValueError()
    except ValueError:
        await message.bot.edit_message_text(
            chat_id=message.chat.id, message_id=data['app_msg_id'],
            text=f"{Templates.BRAND_HEADER}\n" + I18n.t("volume_error", user.language, min=data['min_qty'], max=data['max_qty']),
            reply_markup=Keyboards.cancel_order(user.language)
        )
        return

    is_eligible_drip = any(x in data['service_name'] for x in ["Followers", "Likes", "Views"])
    await state.update_data(quantity=qty)
    
    if is_eligible_drip:
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text=I18n.t("btn_standard", user.language), callback_data="drip_no"),
            types.InlineKeyboardButton(text=I18n.t("btn_drip_feed", user.language), callback_data="drip_yes")
        )
        await message.bot.edit_message_text(
            chat_id=message.chat.id, message_id=data['app_msg_id'],
            text=I18n.t("drip_feed_ask", user.language),
            reply_markup=builder.as_markup()
        )
        await state.set_state(OrderStates.waiting_for_drip_feed)
    else:
        await proceed_to_confirmation(message.bot, message.chat.id, state, user)

@router.callback_query(OrderStates.waiting_for_drip_feed, F.data == "drip_no")
async def process_no_drip(callback: types.CallbackQuery, state: FSMContext, user: User):
    await callback.answer()
    await state.update_data(is_drip_feed=0)
    await proceed_to_confirmation(callback.bot, callback.message.chat.id, state, user)

@router.callback_query(OrderStates.waiting_for_drip_feed, F.data == "drip_yes")
async def process_yes_drip(callback: types.CallbackQuery, state: FSMContext, user: User):
    await callback.answer()
    await state.update_data(is_drip_feed=1)
    await callback.message.edit_text(
        I18n.t("drip_feed_runs", user.language),
        reply_markup=Keyboards.cancel_order(user.language)
    )
    await state.set_state(OrderStates.waiting_for_runs)

@router.message(OrderStates.waiting_for_runs)
async def process_runs(message: types.Message, state: FSMContext, user: User):
    await cleanup_user_input(message)
    data = await state.get_data()
    try:
        runs = int(message.text)
        if not (2 <= runs <= 100): raise ValueError()
        await state.update_data(runs=runs)
        await message.bot.edit_message_text(
            chat_id=message.chat.id, message_id=data.get('app_msg_id'),
            text=I18n.t("drip_feed_interval", user.language),
            reply_markup=Keyboards.cancel_order(user.language)
        )
        await state.set_state(OrderStates.waiting_for_interval)
    except Exception:
        pass

@router.message(OrderStates.waiting_for_interval)
async def process_interval(message: types.Message, state: FSMContext, user: User):
    await cleanup_user_input(message)
    data = await state.get_data()
    try:
        interval = int(message.text)
        if not (10 <= interval <= 1440): raise ValueError()
        await state.update_data(interval=interval)
        await proceed_to_confirmation(message.bot, message.chat.id, state, user)
    except Exception:
        pass

async def proceed_to_confirmation(bot, chat_id: int, state: FSMContext, user: User):
    data = await state.get_data()
    qty = data['quantity']
    runs = data.get('runs', 1)
    is_drip = data.get('is_drip_feed', 0)
    
    total_qty = qty * runs if is_drip else qty
    price, discount = OrderService.calculate_price(total_qty, data['rate'], user.tier)
    await state.update_data(total_price=price, discount=discount, total_qty=total_qty)
    
    if user.balance < price:
        await bot.edit_message_text(
            chat_id=chat_id, message_id=data['app_msg_id'],
            text=I18n.t("insufficient_balance", user.language, required=price, current=user.balance),
            reply_markup=Keyboards.back_to_wallet(user.language)
        )
        await state.clear()
    else:
        await bot.edit_message_text(
            chat_id=chat_id, message_id=data['app_msg_id'],
            text=Templates.order_summary_credit(data['service_name'], total_qty, price, user.balance, user.tier, user.language),
            reply_markup=Keyboards.confirm_order(user.language)
        )
        await state.set_state(OrderStates.confirm_order)

@router.callback_query(OrderStates.confirm_order, F.data == "order_confirm")
async def finalize_order(callback: types.CallbackQuery, state: FSMContext, user: User):
    await callback.answer("⏳ Processing...")
    data = await state.get_data()
    
    async with async_session() as session:
        db_user = await session.get(User, user.id)
        if db_user.balance < data['total_price']:
            await callback.message.edit_text(I18n.t("payment_rejected", user.language))
            return

        db_user.balance -= data['total_price']
        db_user.total_spent += data['total_price']
        if db_user.total_spent >= 2000: db_user.tier = "ELITE"
        elif db_user.total_spent >= 500: db_user.tier = "GOLD"
        elif db_user.total_spent >= 100: db_user.tier = "SILVER"

        try:
            provider = smm_router.get_provider()
            resp = await provider.submit_order(
                service_id=data['service_id'], link=data['target_url'],
                quantity=data.get('quantity'), comments=data.get('comments_list'),
                drip_feed=bool(data.get('is_drip_feed')), runs=data.get('runs'), interval=data.get('interval')
            )
            
            new_order = Order(
                user_id=user.id, tiktok_url=data['target_url'],
                service_id=data['service_id'], comment_count=data.get('total_qty', data.get('quantity', 0)),
                total_price=data['total_price'], status=OrderStatus.PROCESSING,
                external_order_id=resp.order_id, provider_name="SMMWiz",
                is_drip_feed=data.get('is_drip_feed', 0), runs=data.get('runs'), interval=data.get('interval')
            )
            session.add(new_order)
            await session.commit()
            await callback.message.edit_text(Templates.order_success(new_order.id, user.language), reply_markup=Keyboards.back_to_main(user.language))
            await state.clear()
        except Exception as e:
            logger.error(f"SMM Submission Error: {e}")
            await callback.message.edit_text(I18n.t("transmission_error", user.language))
            db_user.balance += data['total_price']
            await session.commit()

@router.callback_query(F.data == "order_cancel")
async def cancel_order_v2(callback: types.CallbackQuery, state: FSMContext, user: User):
    await callback.answer()
    await state.clear()
    await update_app_screen(callback.message, Templates.welcome(callback.from_user.first_name, user.tier, user.language), Keyboards.main_menu(user.language))
