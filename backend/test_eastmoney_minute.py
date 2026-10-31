import requests

tests = {
    "德国DAX":  "100.GDAXI",
    "法国CAC":  "100.FCHI",
    "日经指数": "100.N225",
    "英国富时": "100.FTSE",
}

for name, secid in tests.items():
    url = "https://push2.eastmoney.com/api/qt/stock/trends2/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
        "ut": "fb5fd1943c7b386f172d6893dbfba10b",
        "ndays": "1",
        "iscr": "1",
        "secid": secid,
    }
    r = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"}, timeout=10)
    d = r.json()
    data = d.get("data")
    trends = data.get("trends", []) if data else []
    print(f"{name:6s} HTTP {r.status_code}  secid={secid:10s}  points={len(trends)}")
    if trends:
        print(f"       首: {trends[0]}")
        print(f"       尾: {trends[-1]}")