import requests

codes = ["sh000001", "sz399001", "sz399006", "usDJI", "usIXIC", "usINX", "hkHSI", "ukFTSE", "deDAX", "frCAC", "jpN225"]
apis = ["minute", "usMinute", "hkMinute"]

for code in codes:
    line = f"{code:8s}"
    for api in apis:
        try:
            url = f"https://web.ifzq.gtimg.cn/appstock/app/{api}/query"
            r = requests.get(url, params={"code": code}, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            d = r.json()
            pts = d.get("data", {}).get(code, {}).get("data", {}).get("data", [])
            line += f"  {api}:{len(pts):4d}"
        except Exception:
            line += f"  {api}:💥"
    print(line)