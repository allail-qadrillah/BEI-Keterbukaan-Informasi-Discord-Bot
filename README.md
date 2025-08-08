# IDX Discord Bot

Bot Discord untuk monitoring pengumuman dari Bursa Efek Indonesia (IDX) dengan filter keyword tertentu.

## Fitur

- Monitoring otomatis pengumuman IDX setiap 6 jam
- Filter keyword: "Pengambilalihan", "Penjelasan atas Pemberitaan Media Massa", "Negosiasi" 
- Exclude "Pasar Negosiasi" dari filter "Negosiasi"
- Anti-duplicate message system
- Pengiriman ke channel Discord yang sesuai
- Format pesan terstruktur dengan link attachment
- Menyimpan pesan ke supabase dan tidak akan mengirimkan pesan duplikasi
- Mengirimkan pesan error ke channel

## Struktur Project

```
idx-discord-bot/
├── src/
│   ├── __init__.py
│   ├── config.py          # Konfigurasi aplikasi
│   ├── api_client.py      # Client untuk IDX API
│   ├── message_parser.py  # Parser untuk processing pesan
│   ├── discord_handler.py # Handler Discord bot
│   └── main.py           # Logic utama aplikasi
├── tests/
│   ├── __init__.py
│   ├── test_api_client.py
│   ├── test_message_parser.py
│   └── test_discord_handler.py
├── lambda_function.py    # Entry point untuk AWS Lambda
├── requirements.txt      # Dependencies
└── README.md
```

## Setup Discord Bot

### 1. Buat Discord Application & Bot

1. Kunjungi [Discord Developer Portal](https://discord.com/developers/applications)
2. Klik "New Application" dan beri nama (misal: "IDX Monitor Bot")
3. Di sidebar kiri, pilih "Bot"
4. Di bagian "Token", klik "Copy" untuk mendapatkan bot token
5. **Simpan token ini dengan aman - jangan dibagikan!**

### 2. Set Bot Permissions

1. Di halaman Bot, scroll ke "Privileged Gateway Intents"
2. Aktifkan:
   - Message Content Intent (jika diperlukan)
   - Server Members Intent (opsional)
3. Di sidebar, pilih "OAuth2" > "URL Generator"
4. Pilih scopes:
   - `bot`
5. Pilih bot permissions:
   - Send Messages
   - View Channels
   - Read Message History
6. Copy generated URL dan buka di browser untuk invite bot ke server

### 3. Setup Server Discord

1. Buat channels sesuai mapping di config:
   - `pengambilalihan-alerts`
   - `pemberitaan-media-massa-alerts` 
   - `negosiasi-alerts`
2. Pastikan bot memiliki permission untuk:
   - View Channel
   - Send Messages
   - Read Message History
3. Catat Guild ID server:
   - Enable Developer Mode di Discord
   - Klik kanan nama server > Copy ID

### 4. Setup Supabase
1. Login Ke supabase, lalu buat project baru dan jalankan perintah ini pada SQL Editor
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
### 5. Environment Variables

Buat file `.env` atau set environment variables:

```env
DISCORD_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_guild_id_here
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_SERVICE_KEY=your_supabase_api_key_here
```

## Installation & Usage

### Local Development

1. Clone repository:
```bash
git clone <repository-url>
cd idx-discord-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export DISCORD_TOKEN="your_bot_token"
export DISCORD_GUILD_ID="your_guild_id"
```

4. Run bot:
```bash
python src/main.py
```

### Testing

Run tests dengan pytest:

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_message_parser.py

# Run with coverage
pytest tests/ --cov=src

# Run with verbose output
pytest tests/ -v
```

### AWS Lambda Deployment

1. **Prepare deployment package:**
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

2. **Create Lambda Function:**
   - Function name: `idx-discord-bot`
   - Runtime: Python 3.9
   - Handler: `lambda_function.lambda_handler`
   - Upload zip file

3. **Set Environment Variables:**
   - `DISCORD_TOKEN`: Bot token dari Discord
   - `DISCORD_GUILD_ID`: ID server Discord

4. **Configure Trigger:**
   - EventBridge (CloudWatch Events)
   - Schedule expression: `rate(6 hours)` atau `cron(0 */6 * * ? *)`

## Konfigurasi

### Mengubah Keyword Filter

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

### Mengubah Channel Mapping

Edit `CHANNEL_MAPPING` di `src/config.py`:

```python
CHANNEL_MAPPING = {
    "pengambilalihan": "pengambilalihan-alerts",
    "penjelasan_media": "pemberitaan-media-massa-alerts", 
    "negosiasi": "negosiasi-alerts",
    "merger": "merger-alerts"  # Untuk keyword baru
}
```

## Format Output

Bot akan mengirim pesan dengan format:

```
**KODE_EMITEN** | Judul Pengumuman | 2025-05-28 23:30:19

**Files:**
• [Nama_File_1.pdf](https://link-to-file.com/file1.pdf)
• [Nama_File_2.pdf](https://link-to-file.com/file2.pdf)
```

## Troubleshooting

### Bot tidak merespons
1. Periksa bot token sudah benar
2. Pastikan bot sudah di-invite ke server dengan permission yang tepat
3. Cek environment variables

### Pesan tidak terkirim
1. Periksa nama channel sudah sesuai dengan mapping
2. Pastikan bot memiliki permission Send Messages di channel
3. Cek log untuk error messages

### Lambda timeout
1. Increase timeout di Lambda configuration (default 15 menit sudah cukup)
2. Optimasi API calls jika diperlukan

### Duplicate messages
Bot otomatis check 5 pesan terakhir untuk avoid duplicate. Jika masih ada duplicate:
1. Increase `HISTORY_LIMIT` di config
2. Periksa logic di `check_message_exists`