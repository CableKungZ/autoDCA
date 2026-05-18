<div align="center">

# 🤖 AutoDCA

**Automated Dollar Cost Averaging bot for Binance and Bitkub**

[![🇹🇭 ภาษาไทย](https://img.shields.io/badge/🇹🇭-ภาษาไทย-blue?style=flat-square)](./README.th.md)

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![Vue.js](https://img.shields.io/badge/Vue-3-4FC08D?logo=vue.js&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)

*100% self-hosted · No cloud dependency · Just `docker compose up -d`*

</div>

---

## ✨ Features

| Feature | Detail |
|---|---|
| 🏦 **Multi-Exchange** | Binance (USDT pairs) and Bitkub (THB pairs) |
| ⏰ **Flexible Schedule** | Daily / Weekly / Monthly / Every N hours |
| 📈 **Buy & Sell** | Market, Limit, Percent of Holdings |
| 📊 **Live Stats** | Avg Cost, Unrealized PnL, Holdings per plan |
| 🔄 **THB/USDT Toggle** | Automatic cross-currency conversion |
| 🔔 **Telegram Alerts** | Notifications for every buy/sell order |
| 🔒 **Secure** | API keys encrypted with Fernet before storage |
| 🌐 **Web UI** | Dashboard, Plans, Orders, Settings |

---

## 🚀 Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Exchange API Keys (Binance and/or Bitkub)

### 1. Clone

```bash
git clone https://github.com/CableKungZ/autoDCA.git
cd autoDCA
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
POSTGRES_PASSWORD=your_strong_password
FERNET_KEY=                   # ← see how to generate below
BINANCE_API_KEY=
BINANCE_API_SECRET=
BITKUB_API_KEY=
BITKUB_API_SECRET=
TELEGRAM_BOT_TOKEN=           # optional
TELEGRAM_CHAT_ID=             # optional
```

**Generate Fernet Key:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Run 🎉

```bash
docker compose up -d
```

> First build takes ~2-5 minutes

### 4. Open

| Service | URL |
|---|---|
| 🌐 Web UI | http://localhost:3333 |
| 📖 API Docs | http://localhost:8888/docs |

---

## ⚙️ Exchange API Keys Setup

<details>
<summary><b>🟡 Binance</b></summary>

1. Go to [Binance API Management](https://www.binance.com/en/my/settings/api-management)
2. Create a new API Key
3. Enable **Spot & Margin Trading** permission
4. Whitelist your server IP → find it at **Settings → Server Public IP**

</details>

<details>
<summary><b>🟢 Bitkub</b></summary>

1. Go to [Bitkub API](https://www.bitkub.com/settings/api)
2. Create a new API Key
3. Enable **Trading** permission
4. Whitelist your server IP → find it at **Settings → Server Public IP**

</details>

---

## 📖 Usage

### Create a DCA Plan
1. Go to **Plans** → click **+ New Plan**
2. Select Exchange → Select Pair → Set amount per order
   - Binance ≥ **5 USDT** · Bitkub ≥ **10 THB**
3. Set Schedule → click **Create**

### Buy Now
Click **Buy Now** on the Plans page to execute immediately without waiting for the schedule.

### Sell
Click **Sell** to open the Sell modal:
- ⚡ **Market** — Sell at current market price instantly
- 🎯 **Limit** — Set a target price to sell at
- **%** **Percent** — Sell a percentage of your holdings

---

## 🐳 Docker Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# View logs
docker compose logs -f api
docker compose logs -f scheduler

# Rebuild after code changes
docker compose up -d --build

# Check status
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
<summary><b>API not responding</b></summary>

```bash
docker compose logs api --tail=50
```

</details>

<details>
<summary><b>Orders stuck at Pending</b></summary>

Go to **Orders** page → click **Clear Pending**

</details>

<details>
<summary><b>Binance / Bitkub 401 Unauthorized</b></summary>

- Check API Key and Secret in `.env`
- Whitelist your server IP (find it at **Settings → Server Public IP**)
- Re-run `docker compose up -d` after editing `.env`

</details>

<details>
<summary><b>Docker build fails (DNS error)</b></summary>

Edit `~/.docker/daemon.json`:
```json
{
  "dns": ["8.8.8.8", "1.1.1.1"]
}
```
Then restart Docker Desktop.

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

| Action | Allowed |
|---|---|
| ✅ Personal use | Yes |
| ✅ Modify / Adapt | Yes (credit required) |
| ✅ Redistribute | Yes (credit required) |
| ❌ Commercial use | **Strictly prohibited** |

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

---

<div align="center">

Made with ☕ by [CableKungZ](https://github.com/CableKungZ)

⭐ Star this repo if you find it useful!

</div>
