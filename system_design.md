# Auto DCA System — System Design

## Overview

ระบบ Auto DCA (Dollar Cost Averaging) สำหรับ Binance และ Bitkub รันบนเครื่อง local 100%
เปิดใช้งานด้วยคำสั่งเดียว: `docker compose up -d`

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Docker Compose                     │
│                                                     │
│  ┌────────────┐  ┌────────────┐  ┌───────────────┐  │
│  │ Scheduler  │  │  API       │  │  Frontend     │  │
│  │(APScheduler│  │ (FastAPI)  │  │ (Vue 3+Vite)  │  │
│  │  :worker)  │  │  :8888     │  │   :3333       │  │
│  └─────┬──────┘  └─────┬──────┘  └───────┬───────┘  │
│        │               │                 │          │
│  ┌─────▼───────────────▼─────────────────▼───────┐  │
│  │            PostgreSQL 16                      │  │
│  │    (orders, plans, logs, rate snapshots)      │  │
│  └───────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────┐  │
│  │         Redis 7 (task lock + queue)           │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
              ↕ HTTPS API calls
       Binance API  /  Bitkub API
              ↕
       Telegram Bot API
```

---

## Tech Stack

| Layer        | Technology              | หมายเหตุ                              |
|---|---|---|
| Language     | Python 3.12             | ecosystem crypto ดี, SDK ครบ          |
| API Server   | FastAPI                 | async, OpenAPI docs built-in          |
| Scheduler    | APScheduler             | cron-style DCA triggers, DB-backed    |
| Exchange     | CCXT                    | unified API สำหรับ Binance + Bitkub  |
| Queue/Lock   | Redis 7                 | ป้องกัน duplicate orders              |
| Database     | PostgreSQL 16           | persist ด้วย Docker named volume      |
| Migrations   | Alembic                 | schema versioning                     |
| Frontend     | Vue 3 + Vite            | TypeScript, Composition API           |
| UI Library   | TailwindCSS + shadcn-vue| component library                     |
| Charts       | ApexCharts              | PnL, rate history charts              |
| State        | Pinia                   | Vue state management                  |
| Logging      | structlog               | structured JSON → file + PostgreSQL   |
| Notification | python-telegram-bot     | bot commands + push notifications     |
| Encryption   | Fernet (cryptography)   | encrypt API keys at rest              |

---

## Docker Compose Services

| Service     | Port  | Image            | หมายเหตุ                         |
|---|---|---|---|
| `api`       | 8888  | backend (custom) | FastAPI REST API                 |
| `scheduler` | —     | backend (custom) | APScheduler worker               |
| `frontend`  | 3333  | frontend (nginx) | Vue 3 SPA                        |
| `postgres`  | 5432  | postgres:16      | named volume: `postgres_data`    |
| `redis`     | 6379  | redis:7-alpine   | named volume: `redis_data`       |

---

## Project Structure

```
autoDCA/
├── docker-compose.yml
├── .env.example
├── system_design.md
├── logs/                              # mounted log volume
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                   # FastAPI app entrypoint
│       ├── config.py                 # settings from .env (Pydantic BaseSettings)
│       ├── database.py               # SQLAlchemy async engine + session
│       ├── models/
│       │   ├── dca_plan.py           # DCA plan config
│       │   ├── order.py              # order execution records
│       │   ├── rate_snapshot.py      # THB/USDT rate history
│       │   └── log_entry.py          # structured log records
│       ├── schemas/                  # Pydantic request/response schemas
│       │   ├── plan.py
│       │   ├── order.py
│       │   ├── stats.py
│       │   └── rate.py
│       ├── routers/
│       │   ├── plans.py              # CRUD + pause/resume/delete
│       │   ├── orders.py             # order history, manual trigger
│       │   ├── stats.py              # statistics + PnL
│       │   └── rates.py              # THB/USDT rate history
│       ├── services/
│       │   ├── exchange.py           # CCXT wrapper (Binance + Bitkub)
│       │   ├── dca_engine.py         # DCA order execution logic
│       │   ├── rate_fetcher.py       # fetch & persist THB/USDT rate
│       │   └── telegram.py           # notification sender + bot handler
│       └── scheduler/
│           └── jobs.py               # APScheduler job definitions
│   └── alembic/                      # DB migrations
│       ├── env.py
│       ├── versions/
│       └── alembic.ini
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── index.html
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    └── src/
        ├── main.ts
        ├── App.vue
        ├── router/
        │   └── index.ts
        ├── stores/
        │   ├── plans.ts
        │   ├── orders.ts
        │   └── stats.ts
        ├── views/
        │   ├── Dashboard.vue         # overview + toggle all/per-plan
        │   ├── Plans.vue             # DCA plan management
        │   ├── Orders.vue            # order history + filters
        │   └── Settings.vue          # API keys + Telegram config
        └── components/
            ├── PnLCard.vue
            ├── AvgCostCard.vue
            ├── RateChart.vue         # THB/USDT history chart
            └── OrderTable.vue
```

---

## Database Schema

### `dca_plans`
| Column         | Type       | Notes                        |
|---|---|---|
| id             | uuid PK    | auto-generated               |
| name           | varchar    | user-friendly label          |
| exchange       | enum       | `binance` / `bitkub`         |
| symbol         | varchar    | e.g. `BTC/USDT`, `BTC/THB`  |
| quote_amount   | numeric    | amount to spend per order    |
| currency       | varchar    | `USDT` / `THB`               |
| schedule_cron  | varchar    | cron expression              |
| status         | enum       | `active` / `paused` / `deleted` |
| max_retries    | int        | default 3                    |
| created_at     | timestamp  |                              |
| updated_at     | timestamp  |                              |

### `orders`
| Column            | Type      | Notes                          |
|---|---|---|
| id                | uuid PK   |                                |
| plan_id           | uuid FK   | → dca_plans.id                 |
| exchange          | enum      |                                |
| symbol            | varchar   |                                |
| side              | enum      | `buy`                          |
| quote_amount      | numeric   | THB or USDT spent              |
| base_amount       | numeric   | coin received                  |
| price             | numeric   | fill price                     |
| cost_per_token    | numeric   | quote_amount / base_amount     |
| thb_usd_rate      | numeric   | THB/USDT rate at order time    |
| exchange_order_id | varchar   | exchange's order ID            |
| status            | enum      | `pending`/`filled`/`failed`/`cancelled` |
| retry_count       | int       | default 0                      |
| error_message     | text      | null if success                |
| executed_at       | timestamp |                                |

### `rate_snapshots`
| Column      | Type      | Notes                         |
|---|---|---|
| id          | serial PK |                               |
| rate        | numeric   | THB per 1 USDT                |
| source      | varchar   | `bitkub` / `bot_api`          |
| recorded_at | timestamp |                               |

### `log_entries`
| Column     | Type      | Notes                          |
|---|---|---|
| id         | serial PK |                               |
| level      | varchar   | `INFO` / `WARNING` / `ERROR`  |
| service    | varchar   | `scheduler` / `api` / `exchange` |
| message    | text      |                               |
| context    | jsonb     | plan_id, order_id, extra data |
| created_at | timestamp |                               |

---

## Key Business Logic

### DCA Engine Flow
```
1. APScheduler triggers job (cron schedule)
2. Acquire Redis lock for plan_id (TTL 60s) → prevent duplicate
3. Load plan from DB, verify status = active
4. Fetch current THB/USDT rate → save snapshot
5. Place market buy order via CCXT
6. Save order record (all cost fields populated)
7. Send Telegram success notification
8. Release Redis lock
   ↓ on error:
9. Increment retry_count
10. If retry_count < max_retries → schedule retry in 5 min
11. If retry_count >= max_retries → mark order failed, send Telegram fail alert
```

### Statistics Calculation
- **Average Cost (DCA Price)** = total_quote_spent / total_base_received
- **Unrealized PnL** = (current_price - avg_cost) × total_base_received
- **Unrealized PnL %** = (current_price - avg_cost) / avg_cost × 100
- **Total Invested THB** = Σ (quote_amount × thb_usd_rate) for THB normalization

All stats support:
- Toggle **All plans combined** vs **per-plan**
- Filter by **exchange** (Binance / Bitkub)
- Filter by **symbol**

### THB/USDT Rate Fetching
- APScheduler job runs every **1 hour**
- Source: Bitkub `USDT/THB` ticker (real market rate)
- Stored in `rate_snapshots` table
- Used for: cross-exchange cost comparison, THB normalization

---

## API Endpoints

### Plans
| Method | Path                        | Description              |
|---|---|---|
| GET    | `/api/plans`                | list all plans           |
| POST   | `/api/plans`                | create new plan          |
| GET    | `/api/plans/{id}`           | get plan details         |
| PATCH  | `/api/plans/{id}`           | update plan config       |
| POST   | `/api/plans/{id}/pause`     | pause plan               |
| POST   | `/api/plans/{id}/resume`    | resume plan              |
| DELETE | `/api/plans/{id}`           | soft-delete plan         |
| POST   | `/api/plans/{id}/trigger`   | manual buy now           |

### Orders
| Method | Path                        | Description              |
|---|---|---|
| GET    | `/api/orders`               | list orders (filter/sort)|
| GET    | `/api/orders/{id}`          | order detail             |
| POST   | `/api/orders/{id}/cancel`   | cancel pending order     |

### Statistics
| Method | Path                        | Description              |
|---|---|---|
| GET    | `/api/stats/summary`        | overall summary          |
| GET    | `/api/stats/summary?plan_id=` | per-plan summary       |
| GET    | `/api/stats/pnl`            | PnL breakdown            |

### Rates
| Method | Path                        | Description              |
|---|---|---|
| GET    | `/api/rates`                | THB/USDT rate history    |
| GET    | `/api/rates/current`        | latest rate              |

---

## Web UI Pages

### Dashboard
- Summary cards: Total Invested, Unrealized PnL, Avg DCA Price, # Active Plans
- Toggle: **All** combined ↔ individual plan selector
- THB/USDT Rate chart (last 30 days)
- Recent orders list (last 10)

### Plans Page
- Table: name, exchange, symbol, schedule, status, avg cost, total invested, action buttons
- **Pause** / **Resume** / **Delete** (confirm dialog) / **Buy Now**
- Create new plan form (modal)

### Orders Page
- Filter: exchange, symbol, status, date range
- Sort: date, price, amount, cost per token
- Columns: date, exchange, symbol, amount spent, coins received, price, cost/token, THB rate, status

### Settings Page
- Binance API Key + Secret (masked, encrypted)
- Bitkub API Key + Secret (masked, encrypted)
- Telegram Bot Token + Chat ID
- Default max retries

---

## Telegram Notifications

### Push Notifications (automatic)
1. **Order Success**
   ```
   ✅ DCA Order Filled
   Exchange: Binance
   Pair: BTC/USDT
   Spent: 10 USDT (≈345 THB)
   Received: 0.000142 BTC
   Price: $70,422
   Avg Cost: $68,150
   ```

2. **Order Failed**
   ```
   ❌ DCA Order Failed (retry 2/3)
   Exchange: Bitkub
   Pair: BTC/THB
   Error: Insufficient balance
   Next retry: 5 minutes
   ```

### Bot Commands
| Command          | Description                        |
|---|---|
| `/summary`       | summary of all plans               |
| `/summary BTC`   | filter summary by symbol           |
| `/status`        | list all active plans              |
| `/pnl`           | current PnL for all holdings       |

---

## Environment Variables

```env
# PostgreSQL
POSTGRES_USER=dca
POSTGRES_PASSWORD=changeme
POSTGRES_DB=autodca

# Redis
REDIS_URL=redis://redis:6379/0

# Encryption (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
FERNET_KEY=

# Binance (stored in DB encrypted, these are initial seed only)
BINANCE_API_KEY=
BINANCE_API_SECRET=

# Bitkub
BITKUB_API_KEY=
BITKUB_API_SECRET=

# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# App
API_PORT=8888
FRONTEND_PORT=3333
LOG_LEVEL=INFO
```

---

## Data Persistence

Docker named volumes ensure data survives restarts:
```yaml
volumes:
  postgres_data:   # all orders, plans, logs, rates
  redis_data:      # optional: persisted queue state
  logs_data:       # structured log files
```

> ⚠️ Data is only lost when running `docker compose down -v` (intentional volume deletion)

---

## Quick Start

```bash
# 1. Copy env file and fill in API keys
cp .env.example .env

# 2. Start all services
docker compose up -d

# 3. Check status
docker compose ps

# 4. Open web UI
open http://localhost:3333

# 5. View logs
docker compose logs -f scheduler
docker compose logs -f api

# Stop (data preserved)
docker compose down

# Stop and delete all data
docker compose down -v
```

---

## Security Notes

- Exchange API keys are encrypted with Fernet before storing in DB
- `.env` file should never be committed to git (add to `.gitignore`)
- Use **read + trade** permissions only on exchange API keys (no withdrawal)
- Redis and PostgreSQL are not exposed to host network by default
