<div align="center">

# 🤖 AutoDCA

**ระบบ Dollar Cost Averaging อัตโนมัติสำหรับ Binance และ Bitkub**

[![🇬🇧 English](https://img.shields.io/badge/🇬🇧-English-blue?style=flat-square)](./README.md)

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![Vue.js](https://img.shields.io/badge/Vue-3-4FC08D?logo=vue.js&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)

*รัน local 100% · ไม่พึ่งพา cloud · `docker compose up -d` แล้วใช้ได้เลย*

</div>

---

## ✨ Features

| Feature | รายละเอียด |
|---|---|
| 🏦 **Multi-Exchange** | Binance (USDT) และ Bitkub (THB) |
| ⏰ **Flexible Schedule** | ทุกวัน / รายสัปดาห์ / รายเดือน / ทุก N ชั่วโมง |
| 📈 **Buy & Sell** | Market, Limit, Percent ของ Holdings |
| 📊 **Live Stats** | Avg Cost, Unrealized PnL, Holdings per plan |
| 🔄 **THB/USDT Toggle** | แปลงค่าข้ามสกุลเงินอัตโนมัติ |
| 🔔 **Telegram Alerts** | แจ้งเตือนทุกคำสั่งซื้อ/ขาย |
| 🔒 **Secure** | API keys เข้ารหัสด้วย Fernet ก่อนเก็บ |
| 🌐 **Web UI** | Dashboard, Plans, Orders, Settings |

---

## 🚀 Quick Start

### สิ่งที่ต้องมี

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Exchange API Keys (Binance และ/หรือ Bitkub)

### 1. Clone

```bash
git clone https://github.com/CableKungZ/autoDCA.git
cd autoDCA
```

### 2. ตั้งค่า Environment

```bash
cp .env.example .env
```

เปิด `.env` แล้วแก้ไข:

```env
POSTGRES_PASSWORD=your_strong_password
FERNET_KEY=                   # ← ดูวิธีสร้างด้านล่าง
BINANCE_API_KEY=
BINANCE_API_SECRET=
BITKUB_API_KEY=
BITKUB_API_SECRET=
TELEGRAM_BOT_TOKEN=           # optional
TELEGRAM_CHAT_ID=             # optional
```

**สร้าง Fernet Key:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. รัน 🎉

```bash
docker compose up -d
```

> ครั้งแรกใช้เวลา build ~2-5 นาที

### 4. เปิดใช้งาน

| Service | URL |
|---|---|
| 🌐 Web UI | http://localhost:3333 |
| 📖 API Docs | http://localhost:8888/docs |

---

## ⚙️ ตั้งค่า Exchange API Keys

<details>
<summary><b>🟡 Binance</b></summary>

1. ไปที่ [Binance API Management](https://www.binance.com/en/my/settings/api-management)
2. สร้าง API Key ใหม่
3. เปิดสิทธิ์ **Enable Spot & Margin Trading**
4. Whitelist IP ของ server → ดู IP ได้ที่ **Settings → Server Public IP**

</details>

<details>
<summary><b>🟢 Bitkub</b></summary>

1. ไปที่ [Bitkub API](https://www.bitkub.com/settings/api)
2. สร้าง API Key ใหม่
3. เปิดสิทธิ์ **Trading**
4. Whitelist IP ของ server → ดู IP ได้ที่ **Settings → Server Public IP**

</details>

---

## 📖 การใช้งาน

### สร้าง DCA Plan
1. ไปที่ **Plans** → คลิก **+ New Plan**
2. เลือก Exchange → เลือก Pair → กำหนดจำนวนเงิน
   - Binance ≥ **5 USDT** · Bitkub ≥ **10 THB**
3. ตั้ง Schedule → กด **Create**

### ซื้อทันที
กดปุ่ม **Buy Now** ในหน้า Plans โดยไม่ต้องรอ schedule

### ขาย
กดปุ่ม **Sell** เลือกรูปแบบ:
- ⚡ **Market** — ขายที่ราคาตลาดทันที
- 🎯 **Limit** — กำหนดราคาที่ต้องการขาย
- **%** **Percent** — ขายเป็น % ของ Holdings

---

## 🐳 Docker Commands

```bash
# รัน
docker compose up -d

# หยุด
docker compose down

# ดู logs
docker compose logs -f api
docker compose logs -f scheduler

# Rebuild หลังแก้ไข code
docker compose up -d --build

# ดู status
docker compose ps
```

---

## 🗂️ Project Structure

```
autoDCA/
├── 🐳 docker-compose.yml
├── 📄 .env.example
├── backend/
│   ├── app/
│   │   ├── models/         # SQLAlchemy models
│   │   ├── routers/        # FastAPI endpoints
│   │   ├── services/       # exchange, dca_engine, telegram
│   │   └── scheduler/      # APScheduler jobs
│   └── alembic/            # DB migrations
└── frontend/
    └── src/
        ├── views/          # Dashboard, Plans, Orders, Settings
        └── components/     # OrderTable, SellModal, SchedulePicker
```

---

## 🔧 Troubleshooting

<details>
<summary><b>API ไม่ตอบสนอง</b></summary>

```bash
docker compose logs api --tail=50
```

</details>

<details>
<summary><b>Order ค้างอยู่ที่ Pending</b></summary>

ไปที่หน้า **Orders** → กด **Clear Pending**

</details>

<details>
<summary><b>Binance / Bitkub 401 Unauthorized</b></summary>

- ตรวจสอบ API Key และ Secret ใน `.env`
- Whitelist IP ของ server (ดู IP ได้ที่ **Settings → Server Public IP**)
- รัน `docker compose up -d` ใหม่หลังแก้ `.env`

</details>

<details>
<summary><b>Docker build ล้มเหลว (DNS error)</b></summary>

แก้ไฟล์ `~/.docker/daemon.json`:
```json
{
  "dns": ["8.8.8.8", "1.1.1.1"]
}
```
แล้ว restart Docker Desktop

</details>

---

## 🛠️ Tech Stack

<div align="center">

| Layer | Technology |
|---|---|
| Backend | Python 3.12 + FastAPI |
| Scheduler | APScheduler |
| Database | PostgreSQL 16 |
| Cache / Lock | Redis 7 |
| Frontend | Vue 3 + Vite + TailwindCSS |
| Reverse Proxy | Nginx |
| Container | Docker Compose |

</div>

---

## 📜 License

This project is licensed under **CC BY-NC 4.0**

| การกระทำ | อนุญาต |
|---|---|
| ✅ ใช้งานส่วนตัว | อนุญาต |
| ✅ ดัดแปลง / แก้ไข | อนุญาต (ต้องระบุ credit) |
| ✅ แจกจ่าย / เผยแพร่ต่อ | อนุญาต (ต้องระบุ credit) |
| ❌ นำไปขาย / ใช้เชิงพาณิชย์ | **ห้ามเด็ดขาด** |

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

---

<div align="center">

Made with ☕ by [CableKungZ](https://github.com/CableKungZ)

⭐ Star this repo if you find it useful!

</div>
