# 🤖 Telegram Groq Bot

Bot Telegram AI yang berfungsi seperti ChatGPT — ringan, cepat, tanpa database,
berjalan sebagai **Serverless Function di Vercel** menggunakan **Webhook**
(bukan polling), dengan **Groq API** sebagai otak AI.

## ✨ Fitur

- Membalas pesan apa pun menggunakan model AI dari Groq (cepat & gratis kuota harian).
- Perintah bawaan: `/start`, `/help`, `/about`, `/ping`.
- Format balasan otomatis ke Markdown Telegram (bold, italic, blok kode, list).
- 100% stateless — **tidak ada database, session, login, atau JWT sama sekali**.
- Modular: pemisahan jelas antara logika Telegram, Groq, dan formatting.
- Penanganan error yang rapi (timeout, gagal koneksi, error API).
- Logging aktivitas (waktu, user, pertanyaan, durasi) tanpa menyimpan isi chat ke database.
- Siap deploy ke Vercel dalam hitungan menit.

## 🧱 Struktur Project

```
telegram-groq-bot/
│
├── api/
│   └── webhook.py          # Entry point Flask (endpoint webhook Telegram)
│
├── services/
│   ├── groq_client.py      # Komunikasi dengan Groq API
│   ├── telegram.py         # Kirim pesan & parsing update Telegram
│   └── formatter.py        # Konversi Markdown AI -> Markdown Telegram
│
├── requirements.txt
├── vercel.json
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## 🔁 Cara Kerja

```
User → Telegram → Webhook (Vercel) → Groq API → Telegram → User
```

Setiap pesan masuk diproses langsung dalam satu request, dijawab oleh Groq,
lalu dikirim kembali. Tidak ada state yang disimpan antar-request.

## 🔑 Environment Variable

| Variable         | Wajib | Keterangan                                              |
|-------------------|:---:|----------------------------------------------------------|
| `BOT_TOKEN`       | ✅  | Token bot dari [@BotFather](https://t.me/BotFather)       |
| `WEBHOOK_URL`     | ✅  | URL publik bot, contoh: `https://xxx.vercel.app/api/webhook` |
| `GROQ_API_KEY`    | ✅  | API key dari [console.groq.com](https://console.groq.com) |
| `GROQ_MODEL`      | ❌  | Default: `llama-3.3-70b-versatile`                        |
| `WEBHOOK_SECRET`  | ❌  | Token tambahan untuk validasi keaslian request webhook    |

Salin `.env.example` menjadi `.env` untuk pengembangan lokal.

## 🚀 Instalasi Lokal

```bash
git clone https://github.com/username/telegram-groq-bot.git
cd telegram-groq-bot

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env          # lalu isi nilainya
python api/webhook.py         # jalan di http://localhost:5000
```

Untuk mencoba webhook secara lokal, gunakan tunneling seperti `ngrok`:

```bash
ngrok http 5000
```

## ☁️ Deploy ke Vercel

1. **Push repository ke GitHub.**

2. **Import project di [vercel.com](https://vercel.com/new)** dan pilih repo ini.

3. **Set Environment Variables** di dashboard Vercel
   (Settings → Environment Variables): `BOT_TOKEN`, `GROQ_API_KEY`,
   `WEBHOOK_URL`, dan opsional `GROQ_MODEL`, `WEBHOOK_SECRET`.

4. **Deploy.** Vercel otomatis mendeteksi `vercel.json` dan menjalankan
   `api/webhook.py` sebagai serverless function Python.

5. Setelah deploy selesai, catat URL production, contoh:
   `https://telegram-groq-bot.vercel.app`

> 💡 Catatan paket Vercel: paket **Hobby** membatasi durasi eksekusi function
> hingga 10 detik, sedangkan **Pro** hingga 60 detik ke atas. Jika Groq API
> lambat merespons pada paket Hobby, pertimbangkan upgrade paket atau gunakan
> model Groq yang lebih ringan.

## 🔗 Cara Set Webhook Telegram

Setelah bot ter-deploy, daftarkan webhook-nya ke Telegram dengan satu request:

```bash
curl -F "url=https://telegram-groq-bot.vercel.app/api/webhook" \
     https://api.telegram.org/bot<BOT_TOKEN>/setWebhook
```

Jika menggunakan `WEBHOOK_SECRET`, tambahkan parameter `secret_token`:

```bash
curl -F "url=https://telegram-groq-bot.vercel.app/api/webhook" \
     -F "secret_token=<WEBHOOK_SECRET>" \
     https://api.telegram.org/bot<BOT_TOKEN>/setWebhook
```

Cek status webhook:

```bash
curl https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo
```

Respons `"ok": true` menandakan webhook sudah aktif dan bot siap menerima pesan.

## 🔐 Cara Mendapatkan Groq API Key

1. Buka [console.groq.com](https://console.groq.com) dan login/daftar.
2. Masuk ke menu **API Keys**.
3. Klik **Create API Key**, beri nama, lalu salin nilainya (diawali `gsk_`).
4. Simpan sebagai `GROQ_API_KEY` di `.env` (lokal) atau Environment Variables (Vercel).

## 💬 Contoh Penggunaan

**User:** `Apa itu Python?`
**Bot:** Python adalah bahasa pemrograman tingkat tinggi yang mudah dibaca dan populer untuk berbagai bidang, mulai dari web hingga AI...

**User:** `Buatkan program kalkulator Python`
**Bot:** Mengirim kode lengkap dalam blok kode yang siap disalin.

**User:** `Jelaskan AI`
**Bot:** Memberikan penjelasan terstruktur dengan poin-poin dan format rapi.

## 🛠️ Troubleshooting

| Masalah                                   | Kemungkinan Penyebab & Solusi |
|--------------------------------------------|-------------------------------|
| Bot tidak membalas sama sekali             | Webhook belum di-set. Cek dengan `getWebhookInfo`. |
| Balasan `⚠️ Terjadi kesalahan saat menghubungi AI` | `GROQ_API_KEY` salah/kadaluarsa, atau kuota Groq habis. Cek dashboard Groq. |
| Balasan `⚠️ Server sedang mengalami gangguan` | Error tak terduga di server — cek log function di dashboard Vercel. |
| Deploy sukses tapi endpoint 500            | Pastikan `BOT_TOKEN` dan `GROQ_API_KEY` sudah diset di Environment Variables Vercel, lalu redeploy. |
| Import `services` gagal di Vercel          | Pastikan `vercel.json` memiliki `includeFiles: ["services/**"]` seperti pada repo ini. |
| Pesan panjang terpotong                    | Telegram membatasi 4096 karakter per pesan; ini ditangani otomatis oleh `formatter.truncate`. |
| Format Markdown berantakan                 | Bot otomatis fallback mengirim teks polos jika parsing Markdown gagal. |

## 🧩 Teknologi yang Digunakan

Python 3.12+, Flask, python-telegram-bot, Requests, python-dotenv, Gunicorn,
Groq API, dan Vercel Serverless Functions.

## 📄 Lisensi

Proyek ini menggunakan [Lisensi MIT](LICENSE) — bebas digunakan, dimodifikasi,
dan didistribusikan.
