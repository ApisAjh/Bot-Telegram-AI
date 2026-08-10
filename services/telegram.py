"""
telegram.py
Modul wrapper untuk mengirim pesan dan mem-parsing update dari Telegram Bot API,
menggunakan library python-telegram-bot.

Catatan penting (serverless): Bot TIDAK di-cache lintas request. Di lingkungan
serverless seperti Vercel, sebuah "warm" function instance bisa dipakai ulang
untuk request berikutnya, sementara httpx client internal python-telegram-bot
terikat ke event loop dari asyncio.run() sebelumnya yang sudah ditutup.
Jika Bot di-cache, request kedua akan gagal dengan error semacam
"Event loop is closed" dan bot terlihat "mati" setelah pesan pertama.
Solusinya: buat instance Bot baru dan inisialisasi/tutup dengan
`async with Bot(...)` pada setiap panggilan, dalam loop yang sama.
"""

import asyncio
import logging

from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError

logger = logging.getLogger("telegram-groq-bot")


def parse_update(data: dict, token: str) -> Update:
    """Mengubah payload JSON webhook Telegram menjadi objek Update."""
    # Tidak butuh koneksi jaringan, jadi Bot() biasa (tanpa async init) sudah aman.
    return Update.de_json(data, Bot(token=token))


async def _send_message_async(
    token: str,
    chat_id: int,
    text: str,
    parse_mode: str | None,
    reply_markup=None,
) -> None:
    async with Bot(token=token) as bot:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )


def send_message(
    token: str,
    chat_id: int,
    text: str,
    parse_mode: str | None = ParseMode.MARKDOWN,
    reply_markup=None,
) -> None:
    """
    Mengirim pesan ke Telegram. Jika gagal karena masalah parsing Markdown,
    otomatis mengirim ulang sebagai teks polos agar pesan tetap sampai ke pengguna.
    """
    try:
        asyncio.run(_send_message_async(token, chat_id, text, parse_mode, reply_markup))
    except TelegramError as exc:
        logger.warning(
            "Gagal mengirim dengan parse_mode=%s (%s). Mencoba tanpa formatting.",
            parse_mode, exc,
        )
        try:
            asyncio.run(_send_message_async(token, chat_id, text, None, reply_markup))
        except TelegramError as exc2:
            logger.error("Gagal mengirim pesan ke Telegram: %s", exc2)
            raise


def get_donate_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard berisi tombol Donate Developer."""
    buttons = [
        [
            InlineKeyboardButton(
                "❤️ Donate Developer ❤️", url="https://t.me/iMstaycalm"
            )
        ]
    ]
    return InlineKeyboardMarkup(buttons)
            
