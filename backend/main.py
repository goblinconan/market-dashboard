import asyncio
import time
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException


from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from fetchers import (
    get_cn_oil_df, get_cn_price, fetch_intl_prices, fetch_exchange_rate, fetch_boc_rates,
    fetch_dxy, fetch_intl_gold, fetch_domestic_gold, fetch_us_treasury_yields, fetch_stock_data,
    fetch_600188_history, fetch_stock_history, fetch_watchlist_quotes, normalize_symbol,
    fetch_stock_name, fetch_stock_minute,
    fetch_forex_history, fetch_dxy_history, fetch_brent_history, fetch_oil95_history,
    fetch_gold_history_intl, fetch_gold_history_domestic, fetch_us_bond_history,
    fetch_fund_watchlist, fetch_fund_history,
    fetch_global_indices_quotes, fetch_global_index_history, GLOBAL_INDICES,
    fetch_index_minute,
    fetch_latest_news_from_mx,
)

REFRESH_INTERVAL = 60
HISTORY_CACHE_SECONDS = 3600

connected_clients = set()
snapshot = {}
snapshot_lock = asyncio.Lock()
_minute_cache = {}
_history_cache = {"data": None, "ts": 0}
_history_cache_by_code = {}

# 全局新闻缓存
_news_cache = {"data": [], "last_update": 0}

def update_news_cache():
    """定时任务：更新新闻缓存"""
    global _news_cache
    print(f"[{time.strftime('%H:%M:%S')}] 🔄 正在更新政经新闻...")
    news_data = fetch_latest_news_from_mx()
    if news_data:
        _news_cache["data"] = news_data
        _news_cache["last_update"] = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] ✅ 新闻更新成功，共 {len(news_data)} 条")

# 配置 APScheduler（每 10 分钟抓取一次）
scheduler = AsyncIOScheduler()
scheduler.add_job(update_news_cache, 'interval', minutes=1, id='news_job')

def build_payload():
    wti, brent = fetch_intl_prices()
    cn_df = get_cn_oil_df()
    mid, buy, sell = fetch_boc_rates()
    exchange_rate = fetch_exchange_rate()
    dxy = fetch_dxy()
    intl_gold = fetch_intl_gold()
    domestic_gold = fetch_domestic_gold()
    yields = fetch_us_treasury_yields()
    stocks = fetch_stock_data()
    watchlist = fetch_watchlist_quotes()
    fund_watchlist = fetch_fund_watchlist()
    global_indices = fetch_global_indices_quotes()

    oil = {"WTI原油": wti, "布伦特原油": brent, "92号汽油(全国均价)": get_cn_price(cn_df, "92"), "95号汽油(全国均价)": get_cn_price(cn_df, "95"), "92号汽油(北京)": get_cn_price(cn_df, "92", "北京"), "95号汽油(广东)": get_cn_price(cn_df, "95", "广东"), "92号汽油(天津)": get_cn_price(cn_df, "92", "天津"), "95号汽油(天津)": get_cn_price(cn_df, "95", "天津")}
    fx = {"离岸人民币(USD/CNH)": exchange_rate, "中行折算价": mid, "中行现汇买入": buy, "中行现汇卖出": sell, "美元指数": dxy}
    gold = {"国际金价(美元/盎司)": intl_gold, "国内金价Au99.99(元/克)": domestic_gold}
    treasury = {"美债2Y": yields.get("2Y"), "美债5Y": yields.get("5Y"), "美债10Y": yields.get("10Y"), "美债30Y": yields.get("30Y")}

    return {
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "sections": [
            {"id": "oil", "title": "油价", "items": oil},
            {"id": "fx", "title": "汇率与美元", "items": fx},
            {"id": "gold", "title": "黄金", "items": gold},
            {"id": "treasury", "title": "美债收益率", "items": treasury},
            {"id": "stocks", "title": "股市与ETF", "items": stocks},            
        ],
        "watchlist": watchlist,
        "funds": fund_watchlist,
        "global_indices": global_indices,
    }

async def refresh_loop():
    global snapshot
    while True:
        try:
            payload = await asyncio.to_thread(build_payload)
            async with snapshot_lock:
                snapshot = payload
            dead = set()
            for ws in connected_clients:
                try: await ws.send_json(payload)
                except Exception: dead.add(ws)
            connected_clients.difference_update(dead)
            print(f"[{time.strftime('%H:%M:%S')}] 已推送 {len(connected_clients)} 个客户端")
        except Exception as e:
            print(f"刷新循环异常: {e}")
        await asyncio.sleep(REFRESH_INTERVAL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 启动新闻抓取（放到后台线程，不阻塞启动）
    asyncio.create_task(asyncio.to_thread(update_news_cache))
    scheduler.start()
    
    # 2. 启动你原有的数据推送循环
    task = asyncio.create_task(refresh_loop())
    
    yield
    
    # 3. 关闭时清理
    task.cancel()
    scheduler.shutdown()

# 全局唯一的 app 定义
app = FastAPI(title="Market Dashboard", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/news/latest")
async def get_latest_news(limit: int = 15):
    """前端获取最新新闻的接口"""
    if not _news_cache["data"]:
        # 如果缓存为空，强制刷新一次
        update_news_cache()
    
    return {
        "updated_at": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(_news_cache["last_update"])),
        "news": _news_cache["data"][:limit]
    }

@app.get("/api/health")
async def health(): return {"status": "ok"}

@app.get("/api/snapshot")
async def get_snapshot():
    async with snapshot_lock: return snapshot

@app.get("/api/minute/{symbol}")
async def get_stock_minute_endpoint(symbol: str):
    try:
        full_code, _ = normalize_symbol(symbol)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    now = time.time()
    cached = _minute_cache.get(full_code)
    if cached and (now - cached["ts"] < 60):
        return cached["data"]
    data = await asyncio.to_thread(fetch_stock_minute, full_code)
    if data: _minute_cache[full_code] = {"data": data, "ts": now}
    return data or []

@app.get("/api/history/600188")
async def get_600188_history():
    now = time.time()
    if _history_cache["data"] is not None and (now - _history_cache["ts"] < HISTORY_CACHE_SECONDS):
        return _history_cache["data"]
    data = await asyncio.to_thread(fetch_600188_history, 365)
    if data:
        _history_cache["data"] = data
        _history_cache["ts"] = now
    return data or []

@app.get("/api/history/{symbol}")
async def get_stock_history_endpoint(symbol: str, days: int = 365):
    try:
        full_code, _ = normalize_symbol(symbol)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    now = time.time()
    stock_name = await asyncio.to_thread(fetch_stock_name, full_code)
    cached = _history_cache_by_code.get(full_code)
    if cached and (now - cached["ts"] < HISTORY_CACHE_SECONDS):
        return {"name": stock_name, "data": cached["data"]}
    data = await asyncio.to_thread(fetch_stock_history, full_code, days)
    if data:
        _history_cache_by_code[full_code] = {"data": data, "ts": now}
    return {"name": stock_name, "data": data or []}

_macro_history_cache = {}
@app.get("/api/macro/history")
async def get_macro_history():
    now = time.time()
    if _macro_history_cache.get("ts") and (now - _macro_history_cache["ts"] < 3600):
        return _macro_history_cache["data"]

    results = await asyncio.gather(
        asyncio.to_thread(fetch_brent_history),
        asyncio.to_thread(fetch_oil95_history),
        asyncio.to_thread(fetch_forex_history),
        asyncio.to_thread(fetch_dxy_history),
        asyncio.to_thread(fetch_gold_history_intl),
        asyncio.to_thread(fetch_gold_history_domestic),
        asyncio.to_thread(fetch_us_bond_history, "美国5年期国债"),
        asyncio.to_thread(fetch_us_bond_history, "美国10年期国债")
    )

    data = {
        "brent": results[0], "oil95": results[1], "forex": results[2], "dxy": results[3],
        "gold_intl": results[4], "gold_domestic": results[5], "us_bond_5y": results[6], "us_bond_10y": results[7],
    }
    _macro_history_cache["data"] = data
    _macro_history_cache["ts"] = now
    return data

_fund_history_cache = {}
@app.get("/api/fund/{code}")
async def get_fund_detail(code: str):
    now = time.time()
    if _fund_history_cache.get(code) and (now - _fund_history_cache[code]["ts"] < 14400):
        return _fund_history_cache[code]["data"]
    data = await asyncio.to_thread(fetch_fund_history, code)
    if data:
        _fund_history_cache[code] = {"data": data, "ts": now}
    return data or []

_global_indices_history_cache = {}
@app.get("/api/global_indices/history")
async def get_global_indices_history(name: str):
    now = time.time()
    if name in _global_indices_history_cache and (now - _global_indices_history_cache[name]["ts"] < 3600):
        return _global_indices_history_cache[name]["data"]

    idx_conf = next((i for i in GLOBAL_INDICES if i["name"] == name), None)
    if not idx_conf:
        return []
        
    data = await asyncio.to_thread(fetch_global_index_history, idx_conf["tx_code"])
    if data:
        _global_indices_history_cache[name] = {"data": data, "ts": now}
    return data or []

# main.py 追加
_global_indices_minute_cache = {}

@app.get("/api/global_indices/minute")
async def get_global_index_minute(name: str):
    """当天分时数据，缓存 60 秒（实时性要求高于历史曲线）"""
    now = time.time()
    cached = _global_indices_minute_cache.get(name)
    if cached and (now - cached["ts"] < 60):
        return cached["data"]

    idx_conf = next((i for i in GLOBAL_INDICES if i["name"] == name), None)
    if not idx_conf:
        return {"date": "", "data": []}

    data = await asyncio.to_thread(fetch_index_minute, idx_conf["tx_code"])
    if data and data.get("data"):
        _global_indices_minute_cache[name] = {"data": data, "ts": now}
    return data

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.add(ws)
    try:
        async with snapshot_lock:
            if snapshot: await ws.send_json(snapshot)
        while True: await ws.receive_text()
    except WebSocketDisconnect:
        connected_clients.discard(ws)
    except Exception:
        connected_clients.discard(ws)