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
        await event.update.callback_query.answer(
            "⚠️ System Error\nPlease restart the bot with /start.",
            show_alert=True
        )

async def update_app_screen(message: types.Message, text: str, reply_markup=None, media_path: str = None):
    """
    Intelligent helper to update the UI. 
    Supports text, caption edits, and media replacement (e.g. reverting to logo).
    """
    from aiogram.types import InputMediaPhoto, FSInputFile
    import os

    try:
        if message.photo:
            if media_path and os.path.exists(media_path):
                # Replace current photo (e.g. QR code) with new one (e.g. logo)
                new_media = InputMediaPhoto(media=FSInputFile(media_path), caption=text)
                await message.edit_media(media=new_media, reply_markup=reply_markup)
            else:
                # Just update the caption
                await message.edit_caption(caption=text, reply_markup=reply_markup)
        else:
            if media_path and os.path.exists(media_path):
                # If it was a text message but we want a photo now
                await message.answer_photo(photo=FSInputFile(media_path), caption=text, reply_markup=reply_markup)
                await message.delete()
            else:
                await message.edit_text(text=text, reply_markup=reply_markup)
    except Exception as e:
        try:
            if media_path and os.path.exists(media_path):
                await message.answer_photo(photo=FSInputFile(media_path), caption=text, reply_markup=reply_markup)
            else:
                await message.answer(text=text, reply_markup=reply_markup)
        except Exception:
            pass
