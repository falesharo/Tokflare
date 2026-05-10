import asyncio
import logging
from sqlalchemy import select
from src.core.config import settings
from src.database.db import async_session
from src.database.models import Order, OrderStatus, Transaction, TransactionType, User
from src.core.payments.nowpayments import NOWPayments
from src.core.services.credits import CreditService
from src.bot.ui.templates import Templates
from src.bot.ui.i18n import I18n
from src.core.admin_config import admin_settings

async def payment_verification_task(bot):
    """
    Background task to verify deposits and track processing orders.
    """
    nowpayments = NOWPayments()
    from src.core.smm.router import smm_router
    
    while True:
        try:
            async with async_session() as session:
                # 1. Check pending DEPOSITS
                stmt = select(Transaction).where(
                    Transaction.type == TransactionType.DEPOSIT,
                    Transaction.status == "waiting"
                )
                result = await session.execute(stmt)
                pending_deposits = result.scalars().all()

                for tx in pending_deposits:
                    status = "waiting"
                    
                    # Fetch user to get their language
                    user = await session.get(User, tx.user_id)
                    lang = user.language if user else "en"

                    # USE PERSISTENT SETTINGS
                    if admin_settings.test_mode:
                        status = "finished"
                        logging.info(f"TEST MODE: Auto-confirming deposit for user {tx.user_id}")
                    elif settings.NOWPAYMENTS_API_KEY and tx.payment_id:
                        status = await nowpayments.check_payment_status(tx.payment_id)
                    
                    if status == "finished":
                        bonus = CreditService.calculate_bonus(tx.amount_usd)
                        await CreditService.add_credits(
                            user_id=tx.user_id, amount=tx.amount_usd,
                            transaction_type=TransactionType.DEPOSIT,
                            session=session, bonus_amount=bonus
                        )
                        tx.status = "completed"
                        await session.commit()
                        
                        await bot.send_message(
                            tx.user_id,
                            f"{Templates.BRAND_HEADER}\n" + 
                            I18n.t("notify_deposit_success", lang, amount=tx.amount_usd, bonus=bonus)
                        )
                        
                    elif status == "failed":
                        tx.status = "failed"
                        await session.commit()
                        await bot.send_message(
                            tx.user_id,
                            f"{Templates.BRAND_HEADER}\n" +
                            I18n.t("notify_deposit_failed", lang, amount=tx.amount_usd)
                        )

                # 2. Check processing orders
                stmt = select(Order).where(Order.status == OrderStatus.PROCESSING)
                result = await session.execute(stmt)
                orders = result.scalars().all()

                for order in orders:
                    try:
                        # Fetch user to get language for notification
                        stmt_u = select(User).where(User.id == order.user_id)
                        res_u = await session.execute(stmt_u)
                        u = res_u.scalar()
                        lang = u.language if u else "en"

                        provider = smm_router.get_provider(order.provider_name)
                        if order.external_order_id:
                            status = await provider.get_status(order.external_order_id)
                            
                            if status.value == "Completed":
                                order.status = OrderStatus.COMPLETED
                                await session.commit()
                                await bot.send_message(
                                    order.user_id,
                                    f"{Templates.BRAND_HEADER}\n" +
                                    I18n.t("notify_order_completed", lang, id=order.id, link=order.tiktok_url)
                                )
                    except Exception as e:
                        logging.error(f"Error checking order #{order.id} status: {e}")

        except Exception as e:
            logging.error(f"Error in verification task: {e}")
            
        await asyncio.sleep(60) # Run every minute
