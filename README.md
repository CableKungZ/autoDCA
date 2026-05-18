# AutoDCA

ระบบ Dollar Cost Averaging อัตโนมัติสำหรับ Binance และ Bitkub รัน local 100% ด้วย Docker

---

## Features

- **Multi-exchange**: Binance (USDT pairs) และ Bitkub (THB pairs)
- **Flexible Schedule**: ทุกวัน / รายสัปดาห์ / รายเดือน / ทุก N ชั่วโมง
- **Sell Orders**: Market, Limit, Percent ของ Holdings
- **Live Stats**: Avg Cost, Unrealized PnL, Holdings per plan
- **THB/USDT Toggle**: แปลงค่าข้ามสกุลเงินอัตโนมัติ
- **Telegram Notifications**: แจ้งเตือนทุกคำสั่งซื้อ/ขาย
- **Web UI**: Dashboard, Plans, Orders, Settings

---

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac/Linux)
- Exchange API Keys (Binance และ/หรือ Bitkub)
- Telegram Bot Token (optional)

---

## Setup

### 1. Clone repository

```bash
git clone https://github.com/CableKungZ/autoDCA.git
cd autoDCA
```

### 2. สร้างไฟล์ .env

```bash
cp .env.example .env
```

แก้ไขไฟล์ `.env`:

```env
# PostgreSQL (เปลี่ยน password)
POSTGRES_USER=dca
POSTGRES_PASSWORD=your_strong_password
POSTGRES_DB=autodca

# Redis
REDIS_URL=redis://redis:6379/0

# Encryption key — สร้างด้วย: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FERNET_KEY=your_fernet_key_here

# Binance (ถ้าใช้)
BINANCE_API_KEY=
BINANCE_API_SECRET=

# Bitkub (ถ้าใช้)
BITKUB_API_KEY=
BITKUB_API_SECRET=

# Telegram (optional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Ports
API_PORT=8888
FRONTEND_PORT=3333
```

### 3. สร้าง Fernet Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

คัดลอก output ไปใส่ใน `FERNET_KEY=` ในไฟล์ `.env`

### 4. ตั้งค่า Exchange API Keys

#### Binance
1. ไปที่ [Binance API Management](https://www.binance.com/en/my/settings/api-management)
2. สร้าง API Key ใหม่
3. เปิดสิทธิ์ **Enable Spot & Margin Trading**
4. Whitelist IP ของ server (ดูได้ใน Settings → Server Public IP หลัง setup)

#### Bitkub
1. ไปที่ [Bitkub API](https://www.bitkub.com/settings/api)
2. สร้าง API Key ใหม่
3. เปิดสิทธิ์ **Trading**
4. Whitelist IP ของ server

### 5. รัน

```bash
docker compose up -d
```

ครั้งแรกจะใช้เวลา build ประมาณ 2-5 นาที

### 6. เข้าใช้งาน

| Service | URL |
|---|---|
| Web UI | http://localhost:3333 |
| API Docs | http://localhost:8888/docs |

---

## การใช้งาน

### สร้าง DCA Plan

1. ไปที่หน้า **Plans** → คลิก **New Plan**
2. เลือก Exchange (Binance / Bitkub)
3. เลือก Trading Pair
4. กำหนดจำนวนเงินต่อครั้ง (Binance ≥ 5 USDT, Bitkub ≥ 10 THB)
5. ตั้ง Schedule (เช่น ทุกวัน 09:00)
6. กด Create

### Buy Now

กดปุ่ม **Buy Now** ในหน้า Plans เพื่อซื้อทันทีโดยไม่รอ schedule

### Sell

กดปุ่ม **Sell** เพื่อเปิด Sell Modal:
- **Market** — ขายที่ราคาตลาดทันที
- **Limit** — กำหนดราคาที่ต้องการขาย
- **Percent** — ขายเป็น % ของ Holdings

---

## Docker Commands

```bash
# รัน
docker compose up -d

# หยุด
docker compose down

# ดู logs
docker compose logs -f api
docker compose logs -f scheduler

# Rebuild (หลังแก้ไข code)
docker compose up -d --build

# ดู status
docker compose ps
```

---

## Project Structure

```
autoDCA/
├── docker-compose.yml
├── .env                    # ← สร้างจาก .env.example
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── models/         # SQLAlchemy models
│       ├── routers/        # FastAPI endpoints
│       ├── services/       # exchange, dca_engine, telegram
│       └── scheduler/      # APScheduler jobs
└── frontend/
    ├── Dockerfile
    └── src/
        ├── views/          # Dashboard, Plans, Orders, Settings
        └── components/     # OrderTable, SellModal, SchedulePicker
```

---

## Troubleshooting

### API ไม่ตอบสนอง
```bash
docker compose logs api --tail=50
```

### Order ค้างอยู่ที่ Pending
ไปที่หน้า **Orders** → กด **Clear Pending**

### Binance/Bitkub 401 Unauthorized
- ตรวจสอบ API Key และ Secret ใน `.env`
- ตรวจสอบว่า Whitelist IP ของ server แล้ว (ดู IP ได้ที่ Settings → Server Public IP)
- รัน `docker compose up -d` ใหม่หลังแก้ `.env`

### Docker build ล้มเหลว (DNS error)
เพิ่ม DNS ใน Docker Desktop settings หรือแก้ไฟล์ `~/.docker/daemon.json`:
```json
{
  "dns": ["8.8.8.8", "1.1.1.1"]
}
```
แล้ว restart Docker Desktop

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 + FastAPI |
| Scheduler | APScheduler |
| Database | PostgreSQL 16 |
| Cache/Lock | Redis 7 |
| Frontend | Vue 3 + Vite + TailwindCSS |
| Reverse Proxy | Nginx |
| Container | Docker Compose |

---

## License

This project is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**

### สรุปสิทธิ์การใช้งาน

| การกระทำ | อนุญาต |
|---|---|
| ใช้งานส่วนตัว | ✅ |
| ดัดแปลง / แก้ไข | ✅ |
| แจกจ่าย / เผยแพร่ต่อ | ✅ (ต้องระบุ credit) |
| นำไปขาย / ใช้เชิงพาณิชย์ | ❌ ห้ามเด็ดขาด |

> ดัดแปลงได้เสรี แต่ห้ามนำไปซื้อขายหรือใช้ประโยชน์เชิงพาณิชย์ทุกรูปแบบ

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

---

## Author

Made with ☕ by [CableKungZ](https://github.com/CableKungZ)
