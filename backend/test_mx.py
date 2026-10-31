import requests
import json

# 换成你申请到的 API Key
MX_APIKEY = "mkt_XaFJ59qKm9TahGWi4iIazfoJjiPBge8-l2hzezW9i7E"
MX_API_URL = "https://mkapi2.dfcfs.com/finskillshub/api/claw/query"

def test_query(query):
    headers = {
        "Content-Type": "application/json",
        "apikey": MX_APIKEY,
    }
    payload = {"toolQuery": query}
    
    print(f"\n--- 正在查询: {query} ---")
    try:
        resp = requests.post(MX_API_URL, headers=headers, json=payload, timeout=20)
        print(f"HTTP {resp.status_code}")
        # 打印美化后的 JSON，方便查看结构
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    # 测试查询 A 股分时
    test_query("查询上证指数今日分时数据")
    
    # 测试查询 英国/欧洲 指数分时
    test_query("查询英国富时100指数今日分时数据")