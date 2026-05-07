import qrcode
import io
from aiogram import types, Router
from aiogram.handlers import ErrorHandler
import logging

logger = logging.getLogger(__name__)
router = Router()

def generate_payment_qr(address: str, amount: float, currency: str) -> io.BytesIO:
    """Generates a QR code for a crypto payment."""
    # Format: currency:address?amount=value
    uri = f"{currency.lower()}:{address}?amount={amount}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

@router.error()
async def error_handler(event: types.ErrorEvent):
    logger.exception(f"Unhandled exception: {event.exception}", exc_info=event.exception)
    
    # Notify user if possible
    if event.update.message:
        await event.update.message.answer(
            "⚠️ <b>An error occurred</b>\n"
            "Our team has been notified. Please try again later or contact support if the issue persists."
        )
    elif event.update.callback_query:
        await event.update.callback_query.message.answer(
            "⚠️ <b>System Error</b>\nPlease restart the bot with /start."
        )
