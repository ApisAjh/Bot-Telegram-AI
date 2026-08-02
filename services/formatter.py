"""
formatter.py
Mengonversi Markdown standar (gaya yang biasa dihasilkan model AI, mis. **bold**)
menjadi format Markdown legacy yang didukung Telegram Bot API (*bold*),
tanpa merusak blok kode.
"""

import re

TELEGRAM_MESSAGE_LIMIT = 4096

_CODE_BLOCK_PATTERN = re.compile(r"(```.*?```)", flags=re.DOTALL)
_BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*")


def to_telegram_markdown(text: str) -> str:
    """Mengubah **bold** menjadi *bold* di luar blok kode. Blok kode dibiarkan apa adanya."""
    if not text:
        return text

    parts = _CODE_BLOCK_PATTERN.split(text)
    result = []
    for part in parts:
        if part.startswith("```") and part.endswith("```"):
            result.append(part)
        else:
            result.append(_BOLD_PATTERN.sub(r"*\1*", part))
    return "".join(result)


def truncate(text: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> str:
    """Memotong teks agar tidak melebihi batas panjang pesan Telegram."""
    if len(text) <= limit:
        return text
    return text[: limit - 20].rstrip() + "\n\n... (dipotong)"
