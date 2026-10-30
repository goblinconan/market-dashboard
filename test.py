import requests
import json

candidates = {
    "英国富时": ["ukFTSE", "znb_UKX"],
    "德国DAX": ["deDAX", "znb_DAX"],
    "法国CAC": ["frCAC", "znb_CAC"],
    "日经指数": ["jpN225", "znb_NKY"],
    "道琼斯": ["usDJI", "int_dji"],
    "纳斯达克": ["usIXIC", "int_nasdaq"],
    "标普500": ["usINX", "int_sp500"],
}

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://finance.qq.com/"
}

for name, codes in candidates.items():
    print("\n" + "=" * 55)
    print(name)

    for code in codes:
        try:
            response = requests.get(
                "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
                params={
                    "_var": "kline_dayqfq",
                    "param": f"{code},day,,,320,qfq"
                },
                headers=headers,
                timeout=10
            )

            raw = response.text.strip()

            if "=" in raw:
                raw = raw.split("=", 1)[1].strip()

            data = json.loads(raw)
            root = data.get("data")

            print(f"\n候选代码：{code}")
            print("接口状态：", data.get("code"))

            if isinstance(root, dict):
                node = root.get(code, {})
                if isinstance(node, dict):
                    rows = node.get("qfqday") or node.get("day") or []
                elif isinstance(node, list):
                    rows = node
                else:
                    rows = []
            else:
                rows = []

            print("K线数量：", len(rows))

            if rows:
                print("第一条：", rows[0])
                print("最后一条：", rows[-1])

        except Exception as e:
            print(f"{code} 请求异常：{repr(e)}")