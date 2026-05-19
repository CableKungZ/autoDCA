import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.routers import plans, orders, stats, rates, logs
from app.ws import manager

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("api_started")
    yield
    logger.info("api_stopped")


app = FastAPI(title="AutoDCA API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plans.router)
app.include_router(orders.router)
app.include_router(stats.router)
app.include_router(rates.router)
app.include_router(logs.router)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()   # keep alive / ping
    except WebSocketDisconnect:
        manager.disconnect(ws)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/system/ip")
async def system_ip():
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("https://api.ipify.org")
            return {"ip": r.text.strip()}
    except Exception:
        return {"ip": "unavailable"}
