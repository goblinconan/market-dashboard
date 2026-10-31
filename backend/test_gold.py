import akshare as ak

try:
    df = ak.futures_foreign_hist(symbol="GC") # 国际黄金
    print("获取成功，数据行数:", len(df))
    print(df.tail(3))
except Exception as e:
    print("获取失败:", repr(e))