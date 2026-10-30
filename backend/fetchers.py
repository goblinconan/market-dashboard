import time
import re
import requests
import akshare as ak
import pandas as pd
import datetime as _dt

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

# ---------- A 股 / 个股 ----------
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

# ---------- 历史数据（股票/分钟） ----------
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
        df['close'] = pd.to_numeric(df['close'], errors="coerce")
        df['volume'] = pd.to_numeric(df['volume'], errors="coerce")
        df['amount'] = df['close'] * df['volume']
        df['avg_price'] = df['amount'].cumsum() / df['volume'].cumsum()
        return [{"time": row['day'].strftime("%H:%M"), "price": round(float(row['close']), 2), "avg_price": round(float(row['avg_price']), 2), "volume": int(row['volume']) if not pd.isna(row['volume']) else 0} for _, row in df.iterrows()]
    except Exception: return []

# ================= 宏观历史曲线终极版（直接解析底层 K 线接口） =================


def _normalize_history_df(
    df,
    date_col_hint=None,
    value_col_hint=None,
    days=365
):
    """
    统一历史数据格式：
    1. 日期格式标准化
    2. 数值格式标准化
    3. 清除无效数据
    4. 按自然日筛选最近一年
    5. 按日期升序排列

    返回格式：[{"date": "...", "value": ...}]
    """

    if df is None or df.empty:
        return []

    date_col = (
        date_col_hint
        if date_col_hint in df.columns
        else df.columns[0]
    )

    value_col = (
        value_col_hint
        if value_col_hint in df.columns
        else df.columns[-1]
    )

    df = df.copy()

    df[date_col] = pd.to_datetime(
        df[date_col],
        errors="coerce"
    )

    df[value_col] = pd.to_numeric(
        df[value_col],
        errors="coerce"
    )

    # 清理无效数据
    df = df.dropna(subset=[date_col, value_col])

    # 排除异常历史日期
    df = df[
        df[date_col] >= pd.Timestamp("2000-01-01")
    ]

    # 日期升序
    df = df.sort_values(date_col)

    # 按自然日筛选最近一年
    if days and days > 0:
        today = pd.Timestamp.today().normalize()
        cutoff = today - pd.Timedelta(days=days)

        df = df[
            (df[date_col] >= cutoff) &
            (df[date_col] <= today)
        ]

    # 转换成前端统一格式
    result = []

    for _, row in df.iterrows():
        result.append({
            "date": row[date_col].strftime("%Y-%m-%d"),
            "value": round(float(row[value_col]), 4)
        })

    return result


def _fetch_eastmoney_kline(secid):
    """通用：请求东方财富底层 K 线 JSON 接口"""
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": secid,
        "klt": "101", "fqt": "1", "lmt": "250", "end": "20500101",
        "fields1": "f1,f2,f3,f4,f5,f6,f7,f8",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://quote.eastmoney.com/"
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        data = resp.json()
        klines = data.get("data", {}).get("klines", [])
        records = []
        for item in klines:
            parts = item.split(",")
            # 东财 K 线格式：日期(0), 开盘(1), 收盘(2), 最高(3), 最低(4)...
            records.append({"date": parts[0], "value": float(parts[2])})
        return records
    except Exception as e:
        print(f"东财K线获取失败 ({secid}): {e}")
        return []


def _fetch_sina_forex_history(symbol, var_name, days=365):
    """
    获取新浪外汇历史日K线
    数据格式：日期,开盘,最高,最低,收盘
    """
    url = (
        "https://vip.stock.finance.sina.com.cn/forex/api/jsonp.php/"
        f"var%20{var_name}=/NewForexService.getDayKLine"
        f"?symbol={symbol}&_=1"
    )

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://finance.sina.com.cn/"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        # 匹配新浪返回的 var 变量及括号中的历史数据
        pattern = (
            rf'var\s+{re.escape(var_name)}\s*=\s*'
            r'\("([\s\S]*?)"\)\s*;?'
        )
        match = re.search(pattern, resp.text)

        if not match:
            print(f"{symbol}：新浪接口数据格式不匹配")
            print("响应开头：", repr(resp.text[:300]))
            return []

        raw_data = match.group(1)
        records = []

        # 新浪使用 | 分隔每个交易日
        for line in raw_data.split("|"):
            parts = line.strip().split(",")

            if len(parts) < 5:
                continue

            try:
                records.append({
                    "date": parts[0],
                    "value": float(parts[4])  # 收盘价
                })
            except (ValueError, TypeError):
                continue

        if not records:
            print(f"{symbol}：没有解析到有效历史数据")
            return []

        df = pd.DataFrame(records)

        # 按自然日筛选最近一年，而不是简单取365个交易日
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        cutoff = pd.Timestamp.today().normalize() - pd.Timedelta(days=days)

        df = df.dropna(subset=["date", "value"])
        df = df[df["date"] >= cutoff]

        result = _normalize_history_df(
            df, "date", "value", days=0
        )

        print(
            f"{symbol}：成功获取 {len(result)} 条历史数据，"
            f"范围：{result[0]['date'] if result else '无'}"
            f" 至 {result[-1]['date'] if result else '无'}"
        )

        return result

    except Exception as e:
        print(f"{symbol} 历史数据获取失败：{repr(e)}")
        return []


def fetch_forex_history():
    """离岸人民币 USD/CNH 历史曲线"""
    return _fetch_sina_forex_history(
        symbol="fx_susdcnh",
        var_name="_fx_susdcnh",
        days=365
    )


def fetch_dxy_history():
    """美元指数 DXY 历史曲线"""
    return _fetch_sina_forex_history(
        symbol="DINIW",
        var_name="_DINIW",
        days=365
    )


def fetch_brent_history():
    try:
        return _normalize_history_df(ak.futures_foreign_hist(symbol="OIL"), "date", "close")
    except Exception: return []

def fetch_oil95_history():
    try:
        return _normalize_history_df(ak.energy_oil_hist(), "调整日期", "汽油价格")
    except Exception: return []

def fetch_gold_history_intl():
    try:
        return _normalize_history_df(ak.futures_foreign_hist(symbol="GC"), "date", "close")
    except Exception: return []

def fetch_gold_history_domestic():
    try:
        return _normalize_history_df(ak.spot_hist_sge(symbol="Au99.99"), "date", "close")
    except Exception: return []

def fetch_us_bond_history(symbol="美国5年期国债"):
    try:
        return _normalize_history_df(ak.bond_gb_us_sina(symbol=symbol), "date", "close")
    except Exception: return []

# ================= 基金功能 =================

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