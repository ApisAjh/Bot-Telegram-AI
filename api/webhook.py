"""
api/webhook.py
Entry point Flask yang menerima webhook dari Telegram, meneruskan pesan ke Groq API,
lalu mengirim balasan kembali ke pengguna. Tidak ada database — semua stateless.
"""

import os
import sys
import time
import logging

# Pastikan folder root project ada di sys.path agar "services" bisa di-import
# dengan benar di lingkungan serverless Vercel.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, request, jsonify  # noqa: E402

from services import groq_client, telegram, formatter  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("telegram-groq-bot")

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")  # opsional, untuk validasi tambahan

START_MESSAGE = (
    "👋 Halo!\n"
    "Selamat datang di Bot Telegram AI.\n\n"
    "Saya siap membantu menjawab berbagai pertanyaan, menjelaskan materi, "
    "membantu pemrograman, menerjemahkan bahasa, memberikan ide, serta "
    "membantu menyelesaikan berbagai tugas.\n\n"
    "💬 Kirim pertanyaan atau pesan apa saja, dan saya akan berusaha memberikan "
    "jawaban terbaik.\n\n"
    "Gunakan /help untuk melihat daftar perintah yang tersedia.\n\n"
    "Selamat menggunakan! 🚀"
)

HELP_MESSAGE = (
    "📖 *Daftar Perintah*\n\n"
    "/start - Memulai bot\n"
    "/help - Menampilkan bantuan\n"
    "/about - Tentang bot ini\n"
    "/ping - Memeriksa status bot\n\n"
    "💬 Selain itu, kirim pesan apa saja dan saya akan menjawab menggunakan AI."
)

ABOUT_MESSAGE = (
    "🤖 *Tentang Bot*\n\n"
    "Bot ini dibangun dengan Python + Flask, berjalan tanpa server "
    "(serverless) di Vercel, dan menggunakan Groq API sebagai otak AI.\n\n"
    "Tidak ada data pengguna yang disimpan ke database apa pun — "
    "setiap pesan diproses langsung dan tidak dicatat secara permanen."
)

ERROR_AI_MESSAGE = (
    "⚠️ Terjadi kesalahan saat menghubungi AI.\n"
    "Silakan coba beberapa saat lagi."
)
ERROR_SERVER_MESSAGE = "⚠️ Server sedang mengalami gangguan."


def handle_command(command: str, chat_id: int) -> None:
    """Menangani perintah bawaan bot (/start, /help, /about, /ping)."""
    if command == "/start":
        telegram.send_message(
            BOT_TOKEN,
            chat_id,
            START_MESSAGE,
            parse_mode=None,
            reply_markup=telegram.get_donate_keyboard(),
        )
    elif command == "/help":
        telegram.send_message(BOT_TOKEN, chat_id, HELP_MESSAGE)
    elif command == "/about":
        telegram.send_message(BOT_TOKEN, chat_id, ABOUT_MESSAGE)
    elif command == "/ping":
        telegram.send_message(
            BOT_TOKEN, chat_id, "🏓 Pong! Bot aktif dan siap digunakan.", parse_mode=None
        )
    else:
        telegram.send_message(
            BOT_TOKEN,
            chat_id,
            "Perintah tidak dikenali. Gunakan /help untuk melihat daftar perintah.",
            parse_mode=None,
        )


def handle_message(text: str, chat_id: int, user) -> None:
    """Menangani pesan biasa: meneruskan ke Groq API lalu membalas ke pengguna."""
    username = user.username or user.first_name or "unknown"
    user_id = user.id
    started_at = time.time()

    logger.info("IN  | user_id=%s username=%s pertanyaan=%r", user_id, username, text[:200])

    try:
        answer = groq_client.ask_groq(text, api_key=GROQ_API_KEY)
        answer = formatter.truncate(formatter.to_telegram_markdown(answer))
        telegram.send_message(BOT_TOKEN, chat_id, answer)
    except groq_client.GroqAPIError as exc:
        logger.error("Groq API error untuk user_id=%s: %s", user_id, exc)
        telegram.send_message(BOT_TOKEN, chat_id, ERROR_AI_MESSAGE, parse_mode=None)
    except Exception:  # noqa: BLE001 - jaring pengaman terakhir, jangan sampai bot mati
        logger.exception("Kesalahan tak terduga untuk user_id=%s", user_id)
        telegram.send_message(BOT_TOKEN, chat_id, ERROR_SERVER_MESSAGE, parse_mode=None)
    finally:
        duration = time.time() - started_at
        logger.info(
            "OUT | user_id=%s username=%s durasi=%.2fdetik", user_id, username, duration
        )


@app.route("/", methods=["GET"])
@app.route("/api/webhook", methods=["GET"])
def health_check():
    """Endpoint sederhana untuk memastikan service hidup (dipakai untuk cek manual)."""
    return jsonify({"status": "ok", "service": "telegram-groq-bot"}), 200


@app.route("/", methods=["POST"])
@app.route("/api/webhook", methods=["POST"])
def webhook():
    """Endpoint utama yang menerima update dari Telegram."""
    if not BOT_TOKEN or not GROQ_API_KEY:
        logger.error("BOT_TOKEN atau GROQ_API_KEY belum diset di environment variable.")
        return jsonify({"ok": False, "error": "server misconfigured"}), 500

    # Validasi opsional: cocokkan header secret token Telegram jika WEBHOOK_SECRET diset.
    if WEBHOOK_SECRET:
        header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if header_secret != WEBHOOK_SECRET:
            logger.warning("Request webhook ditolak: secret token tidak cocok.")
            return jsonify({"ok": False}), 403

    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"ok": False, "error": "invalid payload"}), 400

        update = telegram.parse_update(data, BOT_TOKEN)
        message = update.message or update.edited_message
        if message is None or not message.text:
            # Update tanpa teks (foto, stiker, dll) — diabaikan dengan aman.
            return jsonify({"ok": True}), 200

        chat_id = message.chat_id
        text = message.text.strip()
        user = message.from_user

        if text.startswith("/"):
            command = text.split()[0].split("@")[0].lower()
            handle_command(command, chat_id)
        else:
            handle_message(text, chat_id, user)

        return jsonify({"ok": True}), 200

    except Exception:  # noqa: BLE001
        logger.exception("Kesalahan saat memproses webhook")
        # Tetap balas 200 agar Telegram tidak mengulang pengiriman update terus-menerus.
        return jsonify({"ok": False}), 200


# Untuk menjalankan secara lokal: python api/webhook.py
if __name__ == "__main__":
    app.run(debug=True, port=5000)
