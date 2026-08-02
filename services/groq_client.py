"""
groq_client.py
Modul untuk berkomunikasi dengan Groq API (OpenAI-compatible endpoint).
Tidak menyimpan riwayat percakapan — setiap pesan diproses secara independen (stateless).
"""

import os
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
REQUEST_TIMEOUT = 25  # detik — mencegah fungsi serverless menggantung terlalu lama

SYSTEM_PROMPT = (
    "Kamu adalah asisten AI yang ramah, jelas, dan membantu di dalam Telegram. "
    "Jawablah dalam Bahasa Indonesia kecuali pengguna meminta bahasa lain. "
    "Gunakan format Markdown yang didukung Telegram: *bold*, _italic_, dan blok kode "
    "dengan tiga backtick untuk kode program. Jawaban harus rapi, terstruktur, "
    "dan mudah dibaca di layar ponsel."
)


class GroqAPIError(Exception):
    """Dilempar ketika terjadi masalah saat menghubungi Groq API."""


def ask_groq(question: str, api_key: str, model: str = DEFAULT_MODEL) -> str:
    """
    Mengirim pertanyaan pengguna ke Groq API dan mengembalikan jawaban teks.

    Raises:
        GroqAPIError: jika API key kosong, koneksi gagal, timeout, atau respons tidak valid.
    """
    if not api_key:
        raise GroqAPIError("GROQ_API_KEY tidak ditemukan di environment variable.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
    }

    try:
        response = requests.post(
            GROQ_API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise GroqAPIError("Timeout saat menghubungi Groq API.") from exc
    except requests.exceptions.ConnectionError as exc:
        raise GroqAPIError("Gagal terhubung ke Groq API (masalah jaringan).") from exc
    except requests.exceptions.HTTPError as exc:
        detail = ""
        try:
            detail = response.json().get("error", {}).get("message", "")
        except Exception:
            pass
        raise GroqAPIError(f"Groq API mengembalikan error: {detail or exc}") from exc
    except requests.exceptions.RequestException as exc:
        raise GroqAPIError(f"Kesalahan request ke Groq API: {exc}") from exc

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except (ValueError, KeyError, IndexError) as exc:
        raise GroqAPIError("Format respons dari Groq API tidak sesuai.") from exc
