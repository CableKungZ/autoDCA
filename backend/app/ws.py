import json
from fastapi import WebSocket
import structlog

logger = structlog.get_logger()


class WSManager:
    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections.append(ws)
        logger.info("ws_connected", total=len(self._connections))

    def disconnect(self, ws: WebSocket):
        self._connections.remove(ws)
        logger.info("ws_disconnected", total=len(self._connections))

    async def broadcast(self, event: str, data: dict | None = None):
        if not self._connections:
            return
        payload = json.dumps({"event": event, "data": data or {}})
        dead = []
        for ws in self._connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections.remove(ws)


manager = WSManager()
