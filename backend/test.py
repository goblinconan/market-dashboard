import requests

tests = ["上证指数", "道琼斯", "纳斯达克", "英国富时", "日经指数", "法国CAC", "德国DAX"]

for name in tests:
    try:
        r = requests.get(
            "http://127.0.0.1:8000/api/global_indices/minute",
            params={"name": name}, timeout=20
        )
        print(f"\n===== {name} =====")
        print(f"HTTP {r.status_code}  content-type={r.headers.get('content-type')}  len={len(r.text)}")
        print(f"raw[:300]: {r.text[:300]!r}")
        if r.headers.get("content-type", "").startswith("application/json") and r.text:
            d = r.json()
            pts = d.get("data", [])
            print(f"date={d.get('date')}  points={len(pts)}")
            if pts:
                print(f"首: {pts[0]}")
                print(f"尾: {pts[-1]}")
    except Exception as e:
        print(f"{name} 💥 {type(e).__name__}: {e}")