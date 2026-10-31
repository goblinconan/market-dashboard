from email.utils import quote
import time
import re
from zoneinfo import ZoneInfo
import requests
import akshare as ak
import pandas as pd
import datetime as _dt
import json
from zoneinfo import ZoneInfo
# 东方财富等国内接口禁走系统代理
_DIRECT = {"http": None, "https": None}

# 在文件顶部随便找个位置加上你的 Key
MX_APIKEY = "mkt_kp1A6_xrQlYEiGkA6WMJr-3jGnwXA3GmvbOVDcJMUZA" # 替换成你真实申请的 Key
MX_API_URL = "https://mkapi2.dfcfs.com/finskillshub/api/claw/query"


# ---------- 缓存 ----------
_cache_cn_df = None
_last_cn_update = 0
_cache_stocks = {"data": {}, "last_update": 0}
STOCK_CACHE_SECONDS = 300
CN_OIL_CACHE_SECONDS = 3600 * 12

WATCHLIST = [
    {"full_code": "sh600188", "pure_code": "600188", "name": "兖矿能源", "type": "股票"},
    {"full_code": "sz000651", "pure_code": "000651", "name": "格力电器", "type": "股票"},
    {"full_code": "sh501227", "pure_code": "501227", "name": "红利LV",   "type": "ETF"},
    {"full_code": "sz002011", "pure_code": "002011", "name": "盾安环境", "type": "股票"},
    {"full_code": "sh518880", "pure_code": "518880", "name": "黄金ETF",  "type": "ETF"},
    {"full_code": "sh513100", "pure_code": "513100", "name": "纳指ETF",  "type": "ETF"},
    {"full_code": "sh603050", "pure_code": "603050", "name": "科林电气", "type": "股票"},
    {"full_code": "sz300212", "pure_code": "300212", "name": "易华录",   "type": "股票"},
    {"full_code": "sh601991", "pure_code": "601991", "name": "大唐发电", "type": "股票"},
    {"full_code": "sz000681", "pure_code": "000681", "name": "视觉中国", "type": "股票"},
]

FUND_WATCHLIST = [
    {"code": "481017", "name": "工银物流产业股票A"},
    {"code": "163804", "name": "中银收益混合A"},
    {"code": "001050", "name": "嘉实低价策略股票"},
    {"code": "000697", "name": "汇添富移动互联股票A"},
    {"code": "007119", "name": "睿远成长价值混合A"},
    {"code": "161222", "name": "国投瑞银白银期货(LOF)A"},
    {"code": "000991", "name": "工银战略转型股票A"},
    {"code": "481001", "name": "工银核心价值混合A"},
    {"code": "001008", "name": "工银国企改革股票"},
]

GLOBAL_INDICES = [
    {"name": "道琼斯",     "sina_code": "int_dji",    "tx_code": "usDJI",    "type": "global"},
    {"name": "纳斯达克",   "sina_code": "int_nasdaq", "tx_code": "usIXIC",   "type": "global"},
    {"name": "标普500",    "sina_code": "int_sp500",  "tx_code": "usINX",    "type": "global"},
    {"name": "英国富时",   "sina_code": "znb_UKX",    "tx_code": "ukFTSE",   "type": "global"},
    {"name": "德国DAX",    "sina_code": "znb_DAX",    "tx_code": "deDAX",    "type": "global"},
    {"name": "法国CAC",    "sina_code": "znb_CAC",    "tx_code": "frCAC",    "type": "global"},
    {"name": "日经指数",   "sina_code": "znb_NKY",    "tx_code": "jpN225",   "type": "global"},
    {"name": "恒生指数",   "sina_code": "rt_hkHSI",   "tx_code": "hkHSI",    "type": "hk"},
    {"name": "上证指数",   "sina_code": "sh000001",   "tx_code": "sh000001", "type": "a_share"},
    {"name": "深证成指",   "sina_code": "sz399001",   "tx_code": "sz399001", "type": "a_share"},
    {"name": "创业板指",   "sina_code": "sz399006",   "tx_code": "sz399006", "type": "a_share"},
]


# ---------- 实时行情 / 国内油价 ----------
def get_cn_oil_df():
    global _cache_cn_df, _last_cn_update
    if _cache_cn_df is None or (time.time() - _last_cn_update > CN_OIL_CACHE_SECONDS):
        try:
            hist_df = ak.energy_oil_hist()
            hist_df["调整日期"] = pd.to_datetime(hist_df["调整日期"], errors="coerce")
            hist_df = hist_df.dropna(subset=["调整日期"]).sort_values("调整日期", ascending=False)
            latest_date = hist_df.iloc[0]["调整日期"].strftime("%Y%m%d")
            detail_df = ak.energy_oil_detail(date=latest_date)
            if detail_df is not None and not detail_df.empty:
                _cache_cn_df = detail_df
                _last_cn_update = time.time()
        except Exception as e:
            print(f"国内油价获取异常: {e}")
    return _cache_cn_df

def get_cn_price(detail_df, grade="92", region=None):
    if detail_df is None: return None
    grade_str = str(grade).strip().replace("#", "")
    target_col = next((c for c in [f"V_{grade_str}", f"V{grade_str}"] if c in detail_df.columns), None)
    if not target_col: return None
    if not region:
        valid = pd.to_numeric(detail_df[target_col], errors="coerce").dropna()
        return round(float(valid.mean()), 2) if not valid.empty else None
    region_col = next((c for c in ["省份", "地区", "城市"] if c in detail_df.columns), None)
    if region_col:
        matched = detail_df[detail_df[region_col].astype(str).str.contains(str(region), na=False)]
        if not matched.empty:
            price = pd.to_numeric(matched.iloc[0][target_col], errors="coerce")
            return round(float(price), 2) if not pd.isna(price) else None
    return None

def fetch_intl_prices():
    def get_price(symbol_code):
        try:
            df = ak.futures_foreign_commodity_realtime(symbol=symbol_code)
            if df is not None and not df.empty:
                row = df.iloc[0]
                for col in ["current_price", "最新价", "最新价格", "price"]:
                    val = row.get(col)
                    if val is not None and not pd.isna(val):
                        return round(float(val), 2)
        except Exception: pass
        return None
    return get_price("CL"), get_price("OIL")

def fetch_exchange_rate():
    try:
        url = "https://hq.sinajs.cn/list=fx_susdcnh"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            parts = resp.text.split('"')[1].split(",")
            if len(parts) > 3: return round(float(parts[3]), 4)
    except Exception: pass
    return None

def fetch_boc_rates():
    try:
        url = "https://www.boc.cn/sourcedb/whpj/index.html"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, timeout=5)
        resp.encoding = "utf-8"
        pattern = r"<td>\s*美元\s*</td>\s*<td>\s*([\d.]+)\s*</td>\s*<td>[\d.]+</td>\s*<td>\s*([\d.]+)\s*</td>\s*<td>[\d.]+</td>\s*<td>\s*([\d.]+)\s*</td>"
        match = re.search(pattern, resp.text)
        if match:
            return round(float(match.group(3)) / 100, 4), round(float(match.group(1)) / 100, 4), round(float(match.group(2)) / 100, 4)
    except Exception: pass
    return None, None, None

def fetch_dxy():
    try:
        url = "https://hq.sinajs.cn/list=DINIW"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            parts = re.search(r'"([^"]*)"', resp.text).group(1).split(",")
            if len(parts) > 1: return round(float(parts[1]), 4)
    except Exception: pass
    return None

def fetch_intl_gold():
    try:
        url = "https://hq.sinajs.cn/list=hf_GC"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            parts = re.search(r'"([^"]*)"', resp.text).group(1).split(",")
            if parts: return round(float(parts[0]), 2)
    except Exception: pass
    return None

def fetch_domestic_gold():
    try:
        df = ak.spot_quotations_sge(symbol="Au99.99")
        if df is not None and not df.empty:
            price = df.iloc[-1]["现价"]
            if not pd.isna(price): return round(float(price), 2)
    except Exception: pass
    return None

def fetch_us_treasury_yields():
    result = {}
    mapping = {"2Y": "美国2年期国债", "5Y": "美国5年期国债", "10Y": "美国10年期国债", "30Y": "美国30年期国债"}
    for key, name in mapping.items():
        try:
            df = ak.bond_gb_us_sina(symbol=name)
            if df is not None and not df.empty:
                val = df.iloc[-1]["close"]
                if not pd.isna(val): result[key] = round(float(val), 3)
        except Exception: pass
    return result

# ---------- A 股 / 个股 / 全球指数 ----------
def fetch_global_indices_quotes():
    """获取全球主要指数的实时行情"""
    codes = [idx["sina_code"] for idx in GLOBAL_INDICES]
    url = f"https://hq.sinajs.cn/list={','.join(codes)}"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}
    parsed = {}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        resp.encoding = "gbk"
        for line in resp.text.split(";"):
            match = re.search(r'hq_str_(\w+)="([^"]*)"', line)
            if match:
                code = match.group(1)
                fields = match.group(2).split(",")
                idx_conf = next((i for i in GLOBAL_INDICES if i["sina_code"] == code), None)
                if not idx_conf or len(fields) < 4: continue
                
                try:
                    if idx_conf["type"] == "global":
                        parsed[code] = {"price": round(float(fields[1]), 2), "change_pct": round(float(fields[3]), 2)}
                    elif idx_conf["type"] == "hk":
                        parsed[code] = {"price": round(float(fields[6]), 2), "change_pct": round(float(fields[8]), 2)}
                    else:
                        prev_close = float(fields[2])
                        price = float(fields[3])
                        pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
                        parsed[code] = {"price": round(price, 2), "change_pct": round(pct, 2)}
                except (ValueError, IndexError):
                    pass
    except Exception: pass
    return [{**idx, "price": parsed.get(idx["sina_code"], {}).get("price"), "change_pct": parsed.get(idx["sina_code"], {}).get("change_pct")} for idx in GLOBAL_INDICES]

def _fetch_tencent_kline(tx_code: str):
    """获取腾讯指数日K线，解析 JSONP 格式"""
    try:
        url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        params = {"_var": "kline_dayqfq", "param": f"{tx_code},day,,,320,qfq"}
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        raw = resp.text.strip()
        if "=" in raw:
            raw = raw.split("=", 1)[1].strip()
        raw = raw.rstrip(";")
        data = json.loads(raw)
        kline_data = data.get("data", {}).get(tx_code, {})
        days = kline_data.get("day") or kline_data.get("qfqday")
        if not days:
            print(f"腾讯K线 {tx_code} 返回为空")
            return []
        records = []
        for item in days:
            if len(item) < 3:
                continue
            try:
                records.append({"date": item[0], "value": float(item[2])})
            except (ValueError, TypeError):
                continue
        return records
    except Exception as e:
        print(f"腾讯K线获取失败 ({tx_code}): {repr(e)}")
        return []

def fetch_global_index_history(tx_code: str):
    """根据指数代码选择历史数据源，统一返回最近365天的 date/value"""
    """根据指数代码选择历史数据源（优先走妙想API）"""
    # 1. 先尝试走妙想 API
    mx_data = _fetch_global_index_history_mx(tx_code)
    if mx_data:
        print(f"✅ [妙想API] 获取 {tx_code} 历史成功, {len(mx_data)} 条")
        return mx_data

    # 2. 如果妙想失败，再退回到之前的 AkShare 接口
    try:
        # ... (保留你原来的 akshare 逻辑，不用动) ...
        print(f"⚠️ [妙想失败] {tx_code} 退回 AkShare 获取历史")

        # 1. 美国主要指数
        us_symbols = {"usDJI": ".DJI", "usIXIC": ".IXIC", "usINX": ".INX"}
        if tx_code in us_symbols:
            df = ak.index_us_stock_sina(symbol=us_symbols[tx_code])
            return _normalize_history_df(df, "date", "close", days=365)

        # 2. 欧洲及日本指数
        global_symbols = {
            "ukFTSE": "英国富时100指数",
            "deDAX": "德国DAX 30种股价指数",
            "frCAC": "法CAC40指数",
            "jpN225": "日经225指数",
        }
        if tx_code in global_symbols:
            df = ak.index_global_hist_sina(symbol=global_symbols[tx_code])
            df = df[pd.to_numeric(df["close"], errors="coerce") > 0].copy()
            return _normalize_history_df(df, "date", "close", days=365)

        # 3. 恒生指数
        if tx_code == "hkHSI":
            df = ak.stock_hk_index_daily_sina(symbol="HSCCI")
            return _normalize_history_df(df, "date", "close", days=365)

        # 4. A股指数：继续使用已经验证成功的腾讯接口
        records = _fetch_tencent_kline(tx_code)
        df = pd.DataFrame(records)
        return _normalize_history_df(df, "date", "value", days=365)

    except Exception as e:
        print(f"全球指数历史数据获取失败 ({tx_code}): {repr(e)}")
        return []

def fetch_tencent_quotes(codes):
    result = {}
    if not codes: return result
    try:
        url = f"http://qt.gtimg.cn/q={','.join(codes)}"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.qq.com/"}
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            for line in resp.text.split(";"):
                match = re.search(r'v_(\w+)="([^"]*)"', line)
                if match:
                    code = match.group(1)
                    fields = match.group(2).split("~")
                    if len(fields) > 3 and fields[3] != "0.00":
                        result[code] = round(float(fields[3]), 2)
    except Exception: pass
    return result

def fetch_nasdaq():
    try:
        url = "https://hq.sinajs.cn/list=gb_ixic"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            parts = re.search(r'"([^"]*)"', resp.text).group(1).split(",")
            if len(parts) > 1: return round(float(parts[1]), 2)
    except Exception: pass
    return None

def fetch_stock_data():
    data = {}
    nasdaq = fetch_nasdaq()
    if nasdaq: data["纳斯达克"] = nasdaq
    index_map = {"sh000001": "上证指数", "sz399001": "深证成指", "sz399006": "创业板指"}
    idx_quotes = fetch_tencent_quotes(list(index_map.keys()))
    for code, label in index_map.items():
        if code in idx_quotes: data[label] = idx_quotes[code]
    return data

def fetch_stock_name(full_code: str) -> str:
    try:
        url = f"https://hq.sinajs.cn/list={full_code}"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}
        resp = requests.get(url, headers=headers, timeout=5)
        resp.encoding = "gbk"
        match = re.search(r'hq_str_\w+="([^"]*)"', resp.text)
        if match and match.group(1):
            name = match.group(1).split(",")[0]
            if name and name != full_code: return name
    except Exception: pass
    return ""

def normalize_symbol(symbol: str):
    s = (symbol or "").strip().lower()
    if not s: raise ValueError("代码不能为空")
    if s.startswith(("sh", "sz")):
        pure = s[2:]
        if pure.isdigit() and len(pure) == 6: return s, pure
        raise ValueError(f"无效代码: {symbol}")
    if s.isdigit() and len(s) == 6:
        first = s[0]
        if first in ("6", "5", "9"): return f"sh{s}", s
        if first in ("0", "1", "2", "3"): return f"sz{s}", s
    raise ValueError(f"无法识别代码: {symbol}")

def fetch_watchlist_quotes():
    codes = [item["full_code"] for item in WATCHLIST]
    url = f"https://hq.sinajs.cn/list={','.join(codes)}"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}
    parsed = {}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        resp.encoding = "gbk"
        if resp.status_code == 200:
            for line in resp.text.split(";"):
                match = re.search(r'hq_str_(\w+)="([^"]*)"', line)
                if match:
                    code = match.group(1)
                    fields = match.group(2).split(",")
                    if len(fields) > 3:
                        try:
                            price = float(fields[3])
                            prev = float(fields[2])
                            if price > 0:
                                change = price - prev if prev > 0 else 0
                                pct = (change / prev) * 100 if prev > 0 else 0
                                parsed[code] = {"price": round(price, 3), "change": round(change, 3), "change_pct": round(pct, 2)}
                        except ValueError: pass
    except Exception: pass
    return [{**item, "price": parsed.get(item["full_code"], {}).get("price"), "change": parsed.get(item["full_code"], {}).get("change"), "change_pct": parsed.get(item["full_code"], {}).get("change_pct")} for item in WATCHLIST]

def fetch_stock_history(full_code: str, days: int = 365):
    end = _dt.date.today()
    start = end - _dt.timedelta(days=days + 120)
    df = None
    for attempt in range(3):
        try:
            df = ak.stock_zh_a_hist_tx(symbol=full_code, start_date=start.strftime("%Y%m%d"), end_date=end.strftime("%Y%m%d"), adjust="qfq")
            if df is not None and not df.empty: break
        except Exception: pass
        time.sleep(2 + attempt * 2)
    if df is None or df.empty: return []
    open_col = next((c for c in ["开盘", "open"] if c in df.columns), None)
    close_col = next((c for c in ["收盘", "close"] if c in df.columns), None)
    high_col = next((c for c in ["最高", "high"] if c in df.columns), None)
    low_col = next((c for c in ["最低", "low"] if c in df.columns), None)
    vol_col = next((c for c in ["成交量", "volume"] if c in df.columns), None)
    date_col = next((c for c in ["日期", "date"] if c in df.columns), None)
    if not all([open_col, close_col, high_col, low_col, vol_col, date_col]): return []
    df = df.sort_values(date_col).reset_index(drop=True)
    df[vol_col] = pd.to_numeric(df[vol_col], errors="coerce") / 100
    df["MA5"] = df[close_col].rolling(5).mean()
    df["MA20"] = df[close_col].rolling(20).mean()
    df["MA60"] = df[close_col].rolling(60).mean()
    cutoff = end - _dt.timedelta(days=days)
    df = df[pd.to_datetime(df[date_col]).dt.date >= cutoff]
    return [{"date": pd.to_datetime(row[date_col]).strftime("%Y-%m-%d"), "open": round(float(row[open_col]), 2), "close": round(float(row[close_col]), 2), "high": round(float(row[high_col]), 2), "low": round(float(row[low_col]), 2), "ma5": round(float(row["MA5"]), 2) if not pd.isna(row["MA5"]) else None, "ma20": round(float(row["MA20"]), 2) if not pd.isna(row["MA20"]) else None, "ma60": round(float(row["MA60"]), 2) if not pd.isna(row["MA60"]) else None, "volume": int(row[vol_col]) if not pd.isna(row[vol_col]) else 0} for _, row in df.iterrows()]

def fetch_600188_history(days: int = 365):
    return fetch_stock_history("sh600188", days)

def fetch_stock_minute(full_code: str):
    try:
        try:
            df = ak.stock_zh_a_minute(symbol=full_code, period='1', adjust='qfq')
        except Exception:
            df = ak.stock_zh_a_minute(symbol=full_code, period='1', adjust='')
        if df is None or df.empty: return []
        df['day'] = pd.to_datetime(df['day'])
        df = df[df['day'].dt.date == df['day'].dt.date.max()].copy()
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        df['amount'] = df['close'] * df['volume']
        df['avg_price'] = df['amount'].cumsum() / df['volume'].cumsum()
        return [{"time": row['day'].strftime("%H:%M"), "price": round(float(row['close']), 2), "avg_price": round(float(row['avg_price']), 2), "volume": int(row['volume']) if not pd.isna(row['volume']) else 0} for _, row in df.iterrows()]
    except Exception: return []

def _normalize_history_df(df, date_col_hint=None, value_col_hint=None, days=365):
    if df is None or df.empty: return []
    date_col = date_col_hint if date_col_hint in df.columns else df.columns[0]
    value_col = value_col_hint if value_col_hint in df.columns else df.columns[-1]
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    df = df.dropna(subset=[date_col, value_col])
    df = df[df[date_col] >= pd.Timestamp("2000-01-01")]
    df = df.sort_values(date_col)
    if days and days > 0:
        today = pd.Timestamp.today().normalize()
        cutoff = today - pd.Timedelta(days=days)
        df = df[(df[date_col] >= cutoff) & (df[date_col] <= today)]
    return [{"date": row[date_col].strftime("%Y-%m-%d"), "value": round(float(row[value_col]), 4)} for _, row in df.iterrows()]

def _fetch_sina_forex_history(symbol, var_name, days=365):
    url = f"https://vip.stock.finance.sina.com.cn/forex/api/jsonp.php/var%20{var_name}=/NewForexService.getDayKLine?symbol={symbol}&_=1"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        pattern = rf'var\s+{re.escape(var_name)}\s*=\s*\("([\s\S]*?)"\)\s*;?'
        match = re.search(pattern, resp.text)
        if not match: return []
        raw_data = match.group(1)
        records = []
        for line in raw_data.split("|"):
            parts = line.strip().split(",")
            if len(parts) >= 5:
                try: records.append({"date": parts[0], "value": float(parts[4])})
                except (ValueError, TypeError): continue
        if not records: return []
        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        cutoff = pd.Timestamp.today().normalize() - pd.Timedelta(days=days)
        df = df.dropna(subset=["date", "value"])
        df = df[df["date"] >= cutoff]
        return _normalize_history_df(df, "date", "value", days=0)
    except Exception as e:
        print(f"{symbol} 历史数据获取失败：{repr(e)}")
        return []

def fetch_forex_history():
    return _fetch_sina_forex_history(symbol="fx_susdcnh", var_name="_fx_susdcnh", days=365)

def fetch_dxy_history():
    return _fetch_sina_forex_history(symbol="DINIW", var_name="_DINIW", days=365)

def fetch_brent_history():
    try: return _normalize_history_df(ak.futures_foreign_hist(symbol="OIL"), "date", "close")
    except Exception: return []

def fetch_oil95_history():
    try: return _normalize_history_df(ak.energy_oil_hist(), "调整日期", "汽油价格")
    except Exception: return []

def fetch_gold_history_intl():
    """使用妙想API获取国际金价（COMEX黄金主力），失败则退回AkShare"""
    headers = {"Content-Type": "application/json", "apikey": MX_APIKEY}
    payload = {"toolQuery": "查询COMEX黄金近一年每天的收盘价"}
    
    try:
        resp = requests.post(MX_API_URL, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        
        data_list = (
    result.get("data", {})
          .get("data", {})
          .get("searchDataResultDTO", {})
          .get("dataTableDTOList", [])
)
        if not data_list:
            raise ValueError("妙想 API 返回空列表")
            
        for dto in data_list:
            table = dto.get("table", {})
            headName = table.get("headName", [])
            # 325898 通常是收盘价
            close_prices = table.get("325898") or table.get("100000000017527")
            if not close_prices:
                continue
                
            records = []
            for date_str, price_str in zip(headName, close_prices):
                try:
                    clean_date = str(date_str).split("(")[0].split(" ")[0]
                    clean_price = str(price_str).replace("美元", "").replace(",", "").replace("点", "")
                    records.append({"date": clean_date, "value": float(clean_price)})
                except (ValueError, TypeError):
                    continue
            
            if records:
                print(f"✅ [妙想API] 获取国际金价成功, {len(records)} 条")
                return records
    except Exception as e:
        print(f"妙想 API 黄金获取失败，退回 AkShare: {repr(e)}")
        
    # 兜底：如果妙想失败，继续用 AkShare
    try: 
        return _normalize_history_df(ak.futures_foreign_hist(symbol="GC"), "date", "close")
    except Exception: 
        return []

def fetch_gold_history_domestic():
    try: return _normalize_history_df(ak.spot_hist_sge(symbol="Au99.99"), "date", "close")
    except Exception: return []

def fetch_us_bond_history(symbol="美国5年期国债"):
    try: return _normalize_history_df(ak.bond_gb_us_sina(symbol=symbol), "date", "close")
    except Exception: return []

def fetch_fund_quote(code: str):
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
        if df is not None and not df.empty:
            return round(float(df.iloc[-1]["单位净值"]), 4)
    except Exception: pass
    return None

def fetch_fund_watchlist():
    return [{"code": f["code"], "name": f["name"], "price": fetch_fund_quote(f["code"])} for f in FUND_WATCHLIST]

def fetch_fund_history(code: str):
    try:
        return _normalize_history_df(ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势"), "净值日期", "单位净值")
    except Exception: return []


# ============================================================
# 指数当天分时：A股/美股/港股走腾讯，德/法/日/英走东方财富
# ============================================================
def _fetch_index_minute_tencent(tx_code: str):
    """A股、美股、港股：腾讯 minute/usMinute，已验证可用"""
    if tx_code.startswith("us"):
        api = "usMinute"
    elif tx_code.startswith(("sh", "sz", "hk")):
        api = "minute"
    else:
        return None  # 非腾讯支持的市场，交给东方财富分支

    try:
        url = f"https://web.ifzq.gtimg.cn/appstock/app/{api}/query"
        params = {"code": tx_code}
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        payload = resp.json()

        idx_data = payload.get("data", {}).get(tx_code, {})
        if not isinstance(idx_data, dict):
            return {"date": "", "data": []}

        minute_info = idx_data.get("data", {}) or {}
        minute_list = minute_info.get("data", []) or []
        date_str = minute_info.get("date", "")

        records = []
        for line in minute_list:
            parts = str(line).split()
            if len(parts) < 2:
                continue
            try:
                t = parts[0]
                records.append({
                    "time": f"{t[:2]}:{t[2:]}" if len(t) == 4 else t,
                    "price": float(parts[1]),
                    "volume": int(float(parts[2])) if len(parts) > 2 and parts[2] else 0,
                })
            except (ValueError, IndexError):
                continue

        return {"date": date_str, "data": records}
    except Exception as e:
        print(f"腾讯分时失败 {tx_code}: {repr(e)}")
        return {"date": "", "data": []}



def _fetch_index_minute_eastmoney(tx_code: str):
    """使用 Yahoo Finance 获取欧洲和日本指数的分钟行情。"""

    print(f"\n---> [Yahoo Finance] 开始请求 {tx_code} --")

    symbol_map = {
        "deDAX": "^GDAXI",
        "frCAC": "^FCHI",
        "jpN225": "^N225",
    }

    symbol = symbol_map.get(tx_code)

    # 英国 FTSE 暂时保留原数据源，不在这里处理
    if not symbol:
        print(f"---> [Yahoo Finance] {tx_code} 暂无配置")
        return {"date": "", "data": []}

    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

        params = {
            "range": "1d",
            "interval": "5m",
        }

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }

        # 使用已经验证成功的 Docker 主机代理
        proxies = {
            "http": "http://host.docker.internal:11888",
            "https": "http://host.docker.internal:11888",
        }

        resp = requests.get(
            url,
            params=params,
            headers=headers,
            proxies=proxies,
            timeout=20,
        )

        print(
            f"---> [Yahoo Finance] {tx_code} "
            f"HTTP状态码: {resp.status_code}"
        )

        resp.raise_for_status()
        payload = resp.json()

        chart = payload.get("chart", {})
        results = chart.get("result")

        if not results:
            print(f"---> [Yahoo Finance] {tx_code} 没有行情数据")
            return {"date": "", "data": []}

        item = results[0]
        timestamps = item.get("timestamp", [])
        quote_list = item.get("indicators", {}).get("quote", [])

        if not timestamps or not quote_list:
            print(f"---> [Yahoo Finance] {tx_code} 行情字段为空")
            return {"date": "", "data": []}

        quote = quote_list[0]
        closes = quote.get("close", [])
        volumes = quote.get("volume", [])

        exchange_timezone = item.get("meta", {}).get(
            "exchangeTimezoneName", "UTC"
        )

        records = []

        for i, timestamp in enumerate(timestamps):
            try:
                price = closes[i] if i < len(closes) else None

                if price is None:
                    continue

                dt = _dt.datetime.fromtimestamp(
                    timestamp,
                    tz=ZoneInfo(exchange_timezone)
                )

                time_str = dt.strftime("%H:%M")

                volume = volumes[i] if i < len(volumes) else None

                records.append({
                    "time": time_str,
                    "price": float(price),
                    "volume": int(volume) if volume is not None else 0,
                })

            except (ValueError, TypeError, IndexError):
                continue
        
        local_date = _dt.datetime.fromtimestamp(
            timestamps[0],
            tz=ZoneInfo(exchange_timezone)
        ).date().isoformat()

        print(
            f"---> [Yahoo Finance] {tx_code} "
            f"解析成功，共 {len(records)} 个点"
        )

        return {
            "date": local_date,
            "data": records,
        }

    except Exception as e:
        print(
            f"---> [Yahoo Finance] {tx_code} "
            f"请求发生异常: {repr(e)}"
        )
        return {"date": "", "data": []}



def fetch_index_minute(tx_code: str):
    """统一入口（唯一版本）：
    - us* / sh* / sz* / hk*  -> 腾讯接口
    - ukFTSE / deDAX / frCAC / jpN225 -> 东方财富 trends2
    """
    # 1. 腾讯分支（A股 / 美股 / 港股）
    tencent_result = _fetch_index_minute_tencent(tx_code)
    if tencent_result is not None:
        return tencent_result

    # 2. 东方财富分支（德 / 法 / 日 / 英）
    em_supported = {"ukFTSE", "deDAX", "frCAC", "jpN225"}
    if tx_code in em_supported:
        return _fetch_index_minute_eastmoney(tx_code)

    return {"date": "", "data": []}

def _fetch_global_index_history_mx(tx_code: str):
    """通过妙想API获取近一年日线数据"""
    # 映射内部代码到妙想的实体名称
    name_map = {
        "sh000001": "上证指数", "sz399001": "深证成指", "sz399006": "创业板指",
        "usDJI": "道琼斯", "usIXIC": "纳斯达克", "usINX": "标普500",
        "ukFTSE": "英国富时100指数", "deDAX": "德国DAX30指数", 
        "frCAC": "法国CAC40指数", "jpN225": "日经225指数", "hkHSI": "恒生指数"
    }
    query_name = name_map.get(tx_code)
    if not query_name:
        return []

    headers = {"Content-Type": "application/json", "apikey": MX_APIKEY}
    payload = {"toolQuery": f"查询{query_name}近一年每天的收盘价"}
    
    try:
        resp = requests.post(MX_API_URL, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        
        data_list = result.get("data", {}).get("dataTableDTOList", [])
        if not data_list:
            return []

        # 遍历找包含收盘价的数据表
        for dto in data_list:
            table = dto.get("table", {})
            headName = table.get("headName", [])
            # 326269=开盘价, 325898=收盘价
            close_prices = table.get("325898") 
            if not close_prices:
                continue
                
            records = []
            for date_str, price_str in zip(headName, close_prices):
                try:
                    # date_str 可能是 "2026-10-30" 或 "2026-10-30(日)"
                    clean_date = str(date_str).split("(")[0].split(" ")[0]
                    # 去除 "点" 等单位
                    clean_price = str(price_str).replace("点", "").replace(",", "")
                    records.append({"date": clean_date, "value": float(clean_price)})
                except (ValueError, TypeError):
                    continue
            
            if records:
                return records
                
    except Exception as e:
        print(f"妙想 API 历史失败 {tx_code}: {repr(e)}")
        
    return []