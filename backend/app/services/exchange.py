import hashlib
import hmac
import time
from urllib.parse import urlencode
import httpx
import structlog

from app.config import get_settings
from cryptography.fernet import Fernet

logger = structlog.get_logger()
settings = get_settings()

BINANCE_BASE = "https://api.binance.com"
BITKUB_BASE = "https://api.bitkub.com"


# ---------------------------------------------------------------------------
# Encryption helpers
# ---------------------------------------------------------------------------

def _fernet() -> Fernet:
    return Fernet(settings.fernet_key.encode())


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()


# ---------------------------------------------------------------------------
# Binance helpers
# ---------------------------------------------------------------------------

def _binance_sign(secret: str, params: dict) -> str:
    """HMAC-SHA256 signature over URL-encoded params."""
    query = urlencode(params)
    return hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()


async def _binance_request(
    method: str,
    path: str,
    api_key: str = "",
    api_secret: str = "",
    params: dict | None = None,
    signed: bool = False,
) -> dict:
    params = dict(params or {})
    headers = {}
    if api_key:
        headers["X-MBX-APIKEY"] = api_key
    if signed:
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = 5000
        params["signature"] = _binance_sign(api_secret, params)

    url = f"{BINANCE_BASE}{path}"
    async with httpx.AsyncClient(timeout=15) as client:
        if method == "GET":
            resp = await client.get(url, params=params, headers=headers)
        else:
            resp = await client.post(url, params=params, headers=headers)
    if not resp.is_success:
        try:
            err = resp.json()
            code = err.get("code", "")
            msg = err.get("msg", resp.text)
        except Exception:
            code, msg = "", resp.text
        logger.error("binance_http_error", status=resp.status_code, code=code, msg=msg, path=path)
        raise ValueError(f"Binance error {code}: {msg}")
    return resp.json()


# ---------------------------------------------------------------------------
# Bitkub helpers
# ---------------------------------------------------------------------------

def _bitkub_sign(secret: str, timestamp: str, method: str, path: str, query: str, body: str) -> str:
    """HMAC-SHA256 over: timestamp + method + path + query + body."""
    payload = timestamp + method + path + ("?" + query if query else "") + body
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


async def _bitkub_request(
    method: str,
    path: str,
    api_key: str = "",
    api_secret: str = "",
    body: dict | None = None,
) -> dict:
    timestamp = str(int(time.time() * 1000))
    body_str = ""
    headers = {"Content-Type": "application/json"}

    if api_key:
        body_str = _json_encode(body) if body else ""
        signature = _bitkub_sign(api_secret, timestamp, method.upper(), path, "", body_str)
        headers.update({
            "X-BTK-TIMESTAMP": timestamp,
            "X-BTK-APIKEY": api_key,
            "X-BTK-SIGN": signature,
        })

    url = f"{BITKUB_BASE}{path}"
    async with httpx.AsyncClient(timeout=15) as client:
        if method == "GET":
            resp = await client.get(url, headers=headers)
        else:
            resp = await client.post(url, content=body_str, headers=headers)
    if not resp.is_success:
        logger.error("bitkub_http_error", status=resp.status_code, body=resp.text, path=path)
    resp.raise_for_status()
    data = resp.json()
    # Bitkub returns error code in data["error"]
    if isinstance(data, dict) and data.get("error", 0) != 0:
        logger.error("bitkub_api_error", error_code=data["error"], response=data, path=path)
        raise ValueError(f"Bitkub error {data['error']}: {data}")
    return data


def _json_encode(obj: dict) -> str:
    import json
    return json.dumps(obj, separators=(",", ":"))


def _bitkub_ticker_items(data) -> list:
    """Normalize Bitkub ticker response to a flat list of ticker dicts."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # {"error": 0, "result": [...]} wrapper
        if "result" in data:
            result = data["result"]
            if isinstance(result, list):
                return result
            if isinstance(result, dict):
                return list(result.values())
        # plain dict keyed by symbol e.g. {"BTC_THB": {...}}
        return list(data.values())
    return []


# ---------------------------------------------------------------------------
# Public: fetch ticker price (with 30s in-memory cache)
# ---------------------------------------------------------------------------

_ticker_cache: dict[str, tuple[float, float]] = {}  # key -> (price, expires_at)
TICKER_CACHE_TTL = 30  # seconds


async def fetch_ticker_price(exchange: str, symbol: str) -> float:
    """Return last price for symbol. symbol format: BTC/USDT or BTC/THB."""
    cache_key = f"{exchange}:{symbol}"
    cached = _ticker_cache.get(cache_key)
    if cached and time.monotonic() < cached[1]:
        return cached[0]

    if exchange == "binance":
        bsymbol = symbol.replace("/", "")
        data = await _binance_request("GET", "/api/v3/ticker/price", params={"symbol": bsymbol})
        price = float(data["price"])
        logger.info("ticker_fetched", exchange=exchange, symbol=symbol, price=price)

    elif exchange == "bitkub":
        bsymbol = symbol.replace("/", "_").upper()
        data = await _bitkub_request("GET", "/api/v3/market/ticker")
        ticker = next((t for t in _bitkub_ticker_items(data) if t.get("symbol", "").upper() == bsymbol), None)
        if not ticker:
            raise ValueError(f"Symbol {bsymbol} not found in Bitkub ticker")
        price = float(ticker["last"])
        logger.info("ticker_fetched", exchange=exchange, symbol=symbol, price=price)

    else:
        raise ValueError(f"Unsupported exchange: {exchange}")

    _ticker_cache[cache_key] = (price, time.monotonic() + TICKER_CACHE_TTL)
    return price


# ---------------------------------------------------------------------------
# Public: fetch THB/USDT rate
# ---------------------------------------------------------------------------

async def fetch_thb_usdt_rate() -> float:
    """Fetch THB per 1 USDT from Bitkub USDT/THB market."""
    data = await _bitkub_request("GET", "/api/v3/market/ticker")
    items = _bitkub_ticker_items(data)
    logger.debug("bitkub_ticker_syms", syms=[t.get("symbol") for t in items[:10]])
    ticker = next((t for t in items if t.get("symbol", "").upper() in ("USDT_THB", "THB_USDT")), None)
    if not ticker:
        raise ValueError(f"USDT/THB ticker not found on Bitkub. Available syms: {[t.get('sym') for t in items[:20]]}")
    rate = float(ticker["last"])
    logger.info("thb_usdt_rate_fetched", rate=rate)
    return rate


# ---------------------------------------------------------------------------
# Public: place market buy order
# ---------------------------------------------------------------------------

async def place_market_buy(
    exchange: str,
    symbol: str,
    quote_amount: float,
    api_key: str,
    api_secret: str,
) -> dict:
    """
    Place a market buy order spending exactly quote_amount of quote currency.

    Returns a normalized dict:
      {
        "exchange_order_id": str,
        "symbol": str,
        "quote_spent": float,
        "base_received": float,
        "avg_price": float,
      }
    """
    if exchange == "binance":
        return await _binance_market_buy(symbol, quote_amount, api_key, api_secret)
    if exchange == "bitkub":
        return await _bitkub_market_buy(symbol, quote_amount, api_key, api_secret)
    raise ValueError(f"Unsupported exchange: {exchange}")


async def _binance_market_buy(symbol: str, quote_amount: float, api_key: str, api_secret: str) -> dict:
    """
    Binance: POST /api/v3/order
    Use quoteOrderQty to spend exactly quote_amount of quote currency.
    Docs: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/trading-endpoints
    """
    bsymbol = symbol.replace("/", "")
    params = {
        "symbol": bsymbol,
        "side": "BUY",
        "type": "MARKET",
        "quoteOrderQty": quote_amount,
    }
    data = await _binance_request("POST", "/api/v3/order", api_key=api_key, api_secret=api_secret, params=params, signed=True)
    logger.info("binance_order_placed", order_id=data["orderId"], symbol=symbol, fills=data.get("fills"))

    # Calculate avg price and base received from fills
    fills = data.get("fills", [])
    base_received = sum(float(f["qty"]) for f in fills)
    quote_spent = sum(float(f["price"]) * float(f["qty"]) for f in fills)
    avg_price = quote_spent / base_received if base_received else 0

    return {
        "exchange_order_id": str(data["orderId"]),
        "symbol": symbol,
        "quote_spent": quote_spent or quote_amount,
        "base_received": base_received,
        "avg_price": avg_price,
    }


async def _bitkub_market_buy(symbol: str, quote_amount: float, api_key: str, api_secret: str) -> dict:
    """
    Bitkub: POST /api/v3/market/place-bid
    Requires amt (THB to spend) and rat (rate). For market order, fetch current price first.
    Docs: https://github.com/bitkub/bitkub-official-api-docs
    """
    bsymbol = symbol.replace("/", "_").lower()

    # Must provide current price for market order
    current_price = await fetch_ticker_price("bitkub", symbol)

    body = {
        "sym": bsymbol,
        "amt": quote_amount,
        "rat": current_price,
        "typ": "market",
    }
    data = await _bitkub_request("POST", "/api/v3/market/place-bid", api_key=api_key, api_secret=api_secret, body=body)
    result = data.get("result", data)
    logger.info("bitkub_order_placed", order_id=result.get("id"), symbol=symbol, full_result=result)

    # Bitkub returns: rec=amount of base received, rat=actual fill price
    # Fall back to estimate if fields missing
    base_received = float(result.get("rec") or (quote_amount / current_price))
    avg_price = float(result.get("rat") or current_price)

    return {
        "exchange_order_id": str(result.get("id", "")),
        "symbol": symbol,
        "quote_spent": quote_amount,
        "base_received": base_received,
        "avg_price": avg_price,
    }


# ---------------------------------------------------------------------------
# Public: place sell order (market or limit)
# ---------------------------------------------------------------------------

async def place_sell(
    exchange: str,
    symbol: str,
    base_amount: float,
    api_key: str,
    api_secret: str,
    order_type: str = "market",   # "market" | "limit"
    limit_price: float | None = None,
) -> dict:
    """
    Place a sell order for base_amount units of base asset.

    Returns normalized dict:
      { exchange_order_id, symbol, base_sold, quote_received, avg_price }
    """
    if exchange == "binance":
        return await _binance_sell(symbol, base_amount, api_key, api_secret, order_type, limit_price)
    if exchange == "bitkub":
        return await _bitkub_sell(symbol, base_amount, api_key, api_secret, order_type, limit_price)
    raise ValueError(f"Unsupported exchange: {exchange}")


async def _binance_sell(symbol: str, base_amount: float, api_key: str, api_secret: str, order_type: str, limit_price: float | None) -> dict:
    bsymbol = symbol.replace("/", "")
    params: dict = {
        "symbol": bsymbol,
        "side": "SELL",
        "quantity": base_amount,
    }
    if order_type == "limit" and limit_price:
        params["type"] = "LIMIT"
        params["price"] = limit_price
        params["timeInForce"] = "GTC"
    else:
        params["type"] = "MARKET"

    data = await _binance_request("POST", "/api/v3/order", api_key=api_key, api_secret=api_secret, params=params, signed=True)
    logger.info("binance_sell_placed", order_id=data["orderId"], symbol=symbol, type=order_type)

    fills = data.get("fills", [])
    base_sold = sum(float(f["qty"]) for f in fills) or base_amount
    quote_received = sum(float(f["price"]) * float(f["qty"]) for f in fills)
    avg_price = quote_received / base_sold if base_sold else (limit_price or 0)

    # For limit orders fills may be empty until filled
    if not fills and order_type == "limit":
        avg_price = limit_price or 0
        quote_received = base_amount * avg_price

    return {
        "exchange_order_id": str(data["orderId"]),
        "symbol": symbol,
        "base_sold": base_sold,
        "quote_received": quote_received,
        "avg_price": avg_price,
        "status": data.get("status", "NEW"),
    }


async def _bitkub_sell(symbol: str, base_amount: float, api_key: str, api_secret: str, order_type: str, limit_price: float | None) -> dict:
    bsymbol = symbol.replace("/", "_").lower()
    current_price = await fetch_ticker_price("bitkub", symbol)
    rat = limit_price if (order_type == "limit" and limit_price) else current_price

    body = {
        "sym": bsymbol,
        "amt": base_amount,   # Bitkub ask: amt = base asset amount
        "rat": rat,
        "typ": order_type,    # "market" or "limit"
    }
    data = await _bitkub_request("POST", "/api/v3/market/place-ask", api_key=api_key, api_secret=api_secret, body=body)
    result = data.get("result", data)
    logger.info("bitkub_sell_placed", order_id=result.get("id"), symbol=symbol, full_result=result)

    avg_price = float(result.get("rat") or rat)
    quote_received = float(result.get("rec") or (base_amount * avg_price))

    return {
        "exchange_order_id": str(result.get("id", "")),
        "symbol": symbol,
        "base_sold": base_amount,
        "quote_received": quote_received,
        "avg_price": avg_price,
        "status": "filled" if order_type == "market" else "pending",
    }
