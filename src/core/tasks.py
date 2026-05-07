import asyncio
import logging
from sqlalchemy import select
from src.database.db import async_session
from src.database.models import Order, OrderStatus
from src.core.payments.nowpayments import NOWPayments

async def payment_verification_task(bot):
    """
    Background task to verify payments and process orders.
    """
    nowpayments = NOWPayments()
    from src.core.smm.router import smm_router
    
    while True:
        try:
            async with async_session() as session:
                # 1. Check pending payments
                stmt = select(Order).where(Order.status == OrderStatus.AWAITING_PAYMENT)
                result = await session.execute(stmt)
                orders = result.scalars().all()
                
                for order in orders:
                    # In a real app, you'd get the actual payment_id from a Transaction model
                    # For this demo, we'll just simulate verification
                    status = await nowpayments.check_payment_status("MOCK_PAY")
                    
                    if status == "finished":
                        logging.info(f"Order #{order.id} paid! Submitting to SMM panel...")
                        order.status = OrderStatus.PAID
                        await session.commit()
                        
                        # Notify user
                        await bot.send_message(
                            order.user_id,
                            f"✅ <b>Payment Confirmed!</b>\nYour order #{order.id} is now being processed."
                        )
                        
                        # Submit to SMM
                        try:
                            provider = smm_router.get_provider(order.provider_name)
                            response = await provider.submit_order("123", order.tiktok_url, order.comments.split('\n'))
                            order.external_order_id = response.order_id
                            order.status = OrderStatus.PROCESSING
                            await session.commit()
                        except Exception as e:
                            logging.error(f"SMM Submission failed for Order #{order.id}: {e}")
                            order.status = OrderStatus.FAILED
                            await session.commit()

                # 2. Check processing orders
                stmt = select(Order).where(Order.status == OrderStatus.PROCESSING)
                result = await session.execute(stmt)
                orders = result.scalars().all()
                
                for order in orders:
                    provider = smm_router.get_provider(order.provider_name)
                    status = await provider.get_status(order.external_order_id)
                    if status.value == "Completed":
                        order.status = OrderStatus.COMPLETED
                        await session.commit()
                        
                        await bot.send_message(
                            order.user_id,
                            f"✨ <b>Order Completed!</b>\nYour TikTok video boost for link <code>{order.tiktok_url}</code> is finished.\n\nThank you for using TokFlare!"
                        )

        except Exception as e:
            logging.error(f"Error in verification task: {e}")
            
        await asyncio.sleep(60) # Run every minute
