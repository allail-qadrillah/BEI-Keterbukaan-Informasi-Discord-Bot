<div align="center">

# 📊 IDX Discord Bot

*Bot Discord untuk monitoring pengumuman keterbukaan informasi dari Bursa Efek Indonesia*

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Discord](https://img.shields.io/badge/Discord-Bot-7289da.svg)](https://discord.com)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

## 🎯 **Tentang Proyek**

Bot Discord ini dirancang untuk memantau pengumuman keterbukaan informasi dari Bursa Efek Indonesia (IDX) berdasarkan kata kunci tertentu yang dapat memengaruhi pergerakan harga saham.

## 📈 **Latar Belakang**

Pergerakan harga saham umumnya dipengaruhi oleh dua emosi utama: **_greed_** (keserakahan/optimisme) dan **_fear_** (ketakutan/pesimisme). Salah satu penyebab kenaikan harga saham yang signifikan adalah adanya rencana pembelian atau pengambilalihan oleh pihak lain. Aksi ini dapat membawa perubahan besar pada arah bisnis emiten — baik menuju perkembangan positif maupun sekadar menjadikannya sebagai "cangkang" untuk menyuntikkan aset dan mengakses pasar modal.

Masalahnya, informasi seperti ini sering kali sudah diketahui lebih dahulu oleh pihak tertentu (*insider*). Mereka terkadang melakukan akumulasi saham pada harga rendah sebelum informasi resmi dirilis di keterbukaan informasi BEI. Ketika berita resmi keluar, barulah pasar merespons dan harga saham melonjak. Fenomena ini dikenal sebagai **Akuisisi** atau **Backdoor Listing**, dengan contoh kasus pada saham ARTO, PANI, KARW, dan PACK.

### 💡 **Peluang untuk Investor Retail**

Sebagai investor retail, kita memang tidak dapat bertindak selayaknya para insider yang memiliki informasi lebih awal. Namun, kita masih memiliki kesempatan untuk mendapatkan keuntungan dengan memantau Keterbukaan Informasi BEI.

Keuntungannya adalah cakupan informasi yang lebih luas. Para insider umumnya hanya memiliki informasi spesifik untuk emiten tertentu saja, tidak untuk seluruh pasar. Sementara itu, platform Keterbukaan Informasi BEI menyediakan informasi untuk semua emiten yang terdaftar.

Tantangannya adalah tidak praktis untuk memantau platform tersebut setiap hari secara manual. Oleh karena itu, bot ini dikembangkan untuk melakukan monitoring secara otomatis berdasarkan kata kunci tertentu yang telah ditentukan, sehingga kita dapat memanfaatkan peluang yang ada dengan lebih efisien.

## ✨ **Fitur Utama**

- 🔄 **Monitoring otomatis** pengumuman IDX setiap jam
- 🎯 **Filter kata kunci**: seperti "Pengambilalihan", "Penjelasan atas Pemberitaan Media Massa", "Negosiasi"
- ❌ **Pengecualian** "Pasar Negosiasi" dari filter "Negosiasi"
- 🚫 **Sistem anti-duplikasi** pesan
- 📨 **Pengiriman otomatis** ke channel Discord yang sesuai
- 📝 **Format pesan terstruktur** dengan tautan attachment
- 💾 **Penyimpanan data** ke Supabase untuk mencegah duplikasi
- ⚠️ **Notifikasi error** ke channel khusus

## 📁 **Struktur Proyek**

```
idx-discord-bot/
├── src/
│   ├── __init__.py
│   ├── config.py           # Konfigurasi aplikasi
│   ├── api_client.py       # Client untuk IDX API
│   ├── message_parser.py   # Parser untuk pemrosesan pesan
│   ├── discord_handler.py  # Handler Discord bot
│   ├── database_handler.py # Handler Supabase
│   └── main.py             # Logika utama aplikasi
├── lambda_function.py      # Entry point untuk AWS Lambda
├── requirements.txt        # Dependencies
└── README.md
```

## 🚀 **Setup Discord Bot**

### 1️⃣ **Buat Discord Application & Bot**

1. Kunjungi [Discord Developer Portal](https://discord.com/developers/applications)
2. Klik "**New Application**" dan beri nama (contoh: "IDX Monitor Bot")
3. Di sidebar kiri, pilih "**Bot**"
4. Di bagian "**Token**", klik "Copy" untuk mendapatkan bot token
5. ⚠️ **Simpan token ini dengan aman - jangan dibagikan!**

### 2️⃣ **Atur Izin Bot**

1. Di halaman Bot, scroll ke "**Privileged Gateway Intents**"
2. Aktifkan:
   - ✅ Message Content Intent (jika diperlukan)
   - ✅ Server Members Intent (opsional)
3. Di sidebar, pilih "**OAuth2**" > "**URL Generator**"
4. Pilih scopes: `bot`
5. Pilih bot permissions:
   - ✅ Send Messages
   - ✅ View Channels
   - ✅ Read Message History
6. Salin URL yang dihasilkan dan buka di browser untuk mengundang bot ke server

### 3️⃣ **Setup Server Discord**

1. Buat channel sesuai mapping di konfigurasi:
   - `pengambilalihan-alerts`
   - `pemberitaan-media-massa-alerts`
   - `negosiasi-alerts`
2. Pastikan bot memiliki izin untuk:
   - ✅ View Channel
   - ✅ Send Messages  
   - ✅ Read Message History
3. Catat Guild ID server:
   - Aktifkan Developer Mode di Discord
   - Klik kanan nama server > Copy ID

### 4️⃣ **Setup Supabase**

1. Login ke Supabase, kemudian buat proyek baru dan jalankan perintah berikut pada SQL Editor:

   ```sql
   -- Create table for storing sent messages
   CREATE TABLE IF NOT EXISTS sent_messages (
      id BIGSERIAL PRIMARY KEY,
      message_hash VARCHAR(64) NOT NULL UNIQUE,
      kode_emiten VARCHAR(10) NOT NULL,
      judul TEXT NOT NULL,
      channel_name VARCHAR(100) NOT NULL,
      message_content TEXT NOT NULL,
      announcement_date TIMESTAMP WITH TIME ZONE,
      sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   -- Create indexes for better performance
   CREATE INDEX IF NOT EXISTS idx_sent_messages_hash ON sent_messages(message_hash);
   CREATE INDEX IF NOT EXISTS idx_sent_messages_kode_emiten ON sent_messages(kode_emiten);
   CREATE INDEX IF NOT EXISTS idx_sent_messages_sent_at ON sent_messages(sent_at);
   CREATE INDEX IF NOT EXISTS idx_sent_messages_channel ON sent_messages(channel_name);

   -- Add comments for documentation
   COMMENT ON TABLE sent_messages IS 'Stores information about messages sent to Discord channels';
   COMMENT ON COLUMN sent_messages.message_hash IS 'SHA-256 hash of kode_emiten and judul for duplicate detection';
   COMMENT ON COLUMN sent_messages.kode_emiten IS 'Stock ticker symbol';
   COMMENT ON COLUMN sent_messages.judul IS 'Announcement title';
   COMMENT ON COLUMN sent_messages.channel_name IS 'Discord channel name where message was sent';
   COMMENT ON COLUMN sent_messages.message_content IS 'Full formatted message content';
   COMMENT ON COLUMN sent_messages.announcement_date IS 'Original announcement date from IDX';
   COMMENT ON COLUMN sent_messages.sent_at IS 'Timestamp when message was sent to Discord';
   ```

2. Buka Project Overview dan dapatkan `Project URL` dan `API KEY`

### 5️⃣ **Environment Variables**

Buat file `.env` atau atur environment variables:

```env
DISCORD_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_guild_id_here
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_SERVICE_KEY=your_supabase_api_key_here
```

## 💻 **Instalasi & Penggunaan**

### **Development Lokal**

1. **Clone repository:**
   ```bash
   git clone <repository-url>
   cd idx-discord-bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Atur environment variables:**
   ```bash
   export DISCORD_TOKEN="your_bot_token"
   export DISCORD_GUILD_ID="your_guild_id"
   ```

4. **Jalankan bot:**
   ```bash
   python src/main.py
   ```

## ☁️ **AWS Lambda Deployment**

Deployment ke AWS Lambda memerlukan server proxy agar tidak diblokir oleh situs IDX (status 403). Oleh karena itu, siapkan domain proxy dan masukkan pada Environment Variable dengan nama `PROXY`, kemudian *uncomment* pada file `main.py` baris 28.

### **Deployment Manual**

1. **Siapkan deployment package:**
   ```bash
   # Create deployment directory
   mkdir deployment
   cd deployment

   # Copy source code
   cp -r ../src .
   cp ../lambda_function.py .

   # Install dependencies
   pip install -r ../requirements.txt -t .

   # Create zip file
   zip -r idx-discord-bot.zip .
   ```

2. **Buat Lambda Function:**
   - Function name: `idx-discord-bot`
   - Runtime: Python 3.9
   - Handler: `lambda_function.lambda_handler`
   - Upload zip file

3. **Atur Environment Variables:**
   - `DISCORD_TOKEN`: Bot token dari Discord
   - `DISCORD_GUILD_ID`: ID server Discord

4. **Konfigurasi Trigger:**
   - EventBridge (CloudWatch Events)
   - Schedule expression: `rate(6 hours)` atau `cron(0 */6 * * ? *)`

### **Deployment Otomatis**

CI/CD Pipeline AWS Lambda telah disiapkan pada file `.github/workflows/lambda.yaml` menggunakan GitHub Actions.

1. **Sesuaikan nama function:**
   - Pada `Deploy to AWS Lambda` di file `lambda.yaml`
   - Ganti nama function sesuai dengan yang Anda miliki

2. **Tambahkan AWS Credentials:**
   - Setelah repository di-push ke GitHub, buka Settings > Secrets and variables > Actions
   - Tambahkan variabel dengan mengklik "New repository secret":
     - `AWS_ACCESS_KEY_ID`
     - `AWS_SECRET_ACCESS_KEY`

3. **Redeploy:**
   - Redeploy GitHub Actions

## 🖥️ **Deployment Virtual Server**

Deployment pada Cloud Data Center (AWS, GCP, Azure) pasti akan mendapatkan status 403 karena IP diblokir. Oleh karena itu, jika Anda tidak memiliki domain IP server proxy, Anda dapat menggunakan Residential Virtual Server (Cloud Server Lokal).

1. **Clone repository ke server dan setup virtual environment**

2. **Buat file `run_bot.sh`:**
   
   Sesuaikan direktori dengan proyek Anda:
   
   ```bash
   #!/bin/bash

   LOG_FILE="/opt/try/BEI-Keterbukaan-Informasi-Discord-Bot/log-output.txt"
   TIMESTAMP="[$(date '+%Y-%m-%d %H:%M:%S')]"

   # Start log
   echo "$TIMESTAMP Starting bot..." >> "$LOG_FILE"

   # Activate virtual environment
   source /opt/try/BEI-Keterbukaan-Informasi-Discord-Bot/venv/bin/activate

   # Run the bot and capture output
   python3 /opt/try/BEI-Keterbukaan-Informasi-Discord-Bot/src/main.py >> "$LOG_FILE" 2>&1
   EXIT_CODE=$?

   # Log result
   if [ $EXIT_CODE -eq 0 ]; then
      echo "$TIMESTAMP Bot ran successfully." >> "$LOG_FILE"
   else
      echo "$TIMESTAMP Bot failed with exit code $EXIT_CODE." >> "$LOG_FILE"
   fi
   ```

3. **Berikan permission:**
   ```bash
   chmod +x /opt/try/run_bot.sh
   ```

4. **Buat cronjob:**
   - Jalankan perintah `crontab -e`
   - Tambahkan perintah berikut untuk dijalankan setiap 4 jam:
     ```cron
     0 */4 * * * /bin/bash /opt/try/BEI-Keterbukaan-Informasi-Discord-Bot/run_bot.sh >> /opt/try/BEI-Keterbukaan-Informasi-Discord-Bot/cron.log 2>&1
     ```

## ⚙️ **Konfigurasi**

### **Mengubah Kata Kunci Filter**

Edit file `src/config.py` di bagian `KEYWORDS`:

```python
KEYWORDS = {
    "pengambilalihan": KeywordConfig(
        include=["Pengambilalihan"]
    ),
    "penjelasan_media": KeywordConfig(
        include=["Penjelasan atas Pemberitaan Media Massa"]
    ),
    "negosiasi": KeywordConfig(
        include=["Negosiasi"],
        exclude=["Pasar Negosiasi", "Kata lain yang ingin diexclude"]
    ),
    # Tambah keyword baru
    "merger": KeywordConfig(
        include=["Merger", "Akuisisi"],
        exclude=["Rencana Merger"]  # Opsional
    )
}
```

### **Mengubah Channel Mapping**

Edit `CHANNEL_MAPPING` di `src/config.py`:

```python
CHANNEL_MAPPING = {
    "pengambilalihan": "pengambilalihan-alerts",
    "penjelasan_media": "pemberitaan-media-massa-alerts", 
    "negosiasi": "negosiasi-alerts",
    "merger": "merger-alerts"  # Untuk keyword baru
}
```

## 📋 **Format Output**

Bot akan mengirim pesan dengan format:

```
**KODE_EMITEN** | Judul Pengumuman | 2025-05-28 23:30:19

**Files:**
• [Nama_File_1.pdf](https://link-to-file.com/file1.pdf)
• [Nama_File_2.pdf](https://link-to-file.com/file2.pdf)
```

## 🛠️ **Troubleshooting**

### **Bot tidak merespons**
1. ✅ Periksa bot token sudah benar
2. ✅ Pastikan bot sudah diundang ke server dengan izin yang tepat
3. ✅ Periksa environment variables

### **Pesan tidak terkirim**
1. ✅ Periksa nama channel sudah sesuai dengan mapping
2. ✅ Pastikan bot memiliki izin Send Messages di channel
3. ✅ Periksa log untuk pesan error

### **Lambda timeout**
1. ✅ Tingkatkan timeout di konfigurasi Lambda (default 15 menit sudah cukup)
2. ✅ Optimisasi API calls jika diperlukan

### **Requests Return 403**
1. ✅ Gunakan Proxy
2. ✅ Jangan deploy di Cloud Data Center seperti AWS, GCP, atau Azure

### **Duplicate messages**
Bot otomatis memeriksa 5 pesan terakhir untuk menghindari duplikasi. Jika masih ada duplikasi:
1. ✅ Tingkatkan `HISTORY_LIMIT` di konfigurasi
2. ✅ Periksa logika di `check_message_exists`

---

<div align="center">

**Made with ❤️ for Indonesian Stock Market Enthusiasts**

*Happy Trading! 📈*

</div>