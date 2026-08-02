"""
telegram.py
Modul wrapper untuk mengirim pesan dan mem-parsing update dari Telegram Bot API,
menggunakan library python-telegram-bot.
"""

import asyncio
import logging

from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.error import TelegramError

logger = logging.getLogger("telegram-groq-bot")

_bot_instances: dict[str, Bot] = {}


def get_bot(token: str) -> Bot:
    """Mengembalikan instance Bot (di-cache per token) agar tidak dibuat berulang kali."""
    if token not in _bot_instances:
        _bot_instances[token] = Bot(token=token)
    return _bot_instances[token]


def parse_update(data: dict, token: str) -> Update:
    """Mengubah payload JSON webhook Telegram menjadi objek Update."""
    return Update.de_json(data, get_bot(token))


def send_message(
    token: str,
    chat_id: int,
    text: str,
    parse_mode: str | None = ParseMode.MARKDOWN,
) -> None:
    """
    Mengirim pesan ke Telegram. Jika gagal karena masalah parsing Markdown,
    otomatis mengirim ulang sebagai teks polos agar pesan tetap sampai ke pengguna.
    """
    bot = get_bot(token)
    try:
        asyncio.run(bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode))
    except TelegramError as exc:
        logger.warning(
            "Gagal mengirim dengan parse_mode=%s (%s). Mencoba tanpa formatting.",
            parse_mode, exc,
        )
        try:
            asyncio.run(bot.send_message(chat_id=chat_id, text=text))
        except TelegramError as exc2:
            logger.error("Gagal mengirim pesan ke Telegram: %s", exc2)
            raise
