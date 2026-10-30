import akshare as ak

indices = {
    "道琼斯": ".DJI",
    "纳斯达克": ".IXIC",
    "标普500": ".INX",
}

for name, symbol in indices.items():
    print("\n" + "=" * 50)
    print("正在测试：", name, symbol)

    try:
        df = ak.index_us_stock_sina(symbol=symbol)

        print("总数据量：", len(df))
        print("字段：", df.columns.tolist())

        if not df.empty:
            print("最早日期：", df["date"].min())
            print("最新日期：", df["date"].max())
            print("最新收盘价：", df.iloc[-1]["close"])

    except Exception as e:
        print("获取失败：", repr(e))