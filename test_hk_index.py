import akshare as ak
import pandas as pd

# 第一步：获取港股指数列表
df = ak.stock_hk_index_spot_sina()

print("港股指数总数：", len(df))
print("字段：", df.columns.tolist())

# 第二步：查找恒生指数
result = df[
    df["名称"].astype(str).str.contains("恒生", na=False)
]

print("\n恒生指数匹配结果：")
print(result.to_string(index=False))

# 第三步：获取恒生指数历史行情
if not result.empty:
    symbol = result.iloc[0]["代码"]

    print("\n使用指数代码：", symbol)

    history = ak.stock_hk_index_daily_sina(
        symbol=str(symbol)
    )

    print("历史数据总量：", len(history))
    print("字段：", history.columns.tolist())

    if not history.empty:
        history["date"] = pd.to_datetime(history["date"])

        one_year_ago = (
            pd.Timestamp.today().normalize()
            - pd.Timedelta(days=365)
        )

        year_data = history[
            history["date"] >= one_year_ago
        ]

        print("最早日期：", history["date"].min())
        print("最新日期：", history["date"].max())
        print("最近一年数据量：", len(year_data))
        print("最新收盘价：", history.iloc[-1]["close"])
else:
    print("没有找到恒生指数")