import akshare as ak

df = ak.index_global_name_table()

print("指数总数：", len(df))
print(df.to_string(index=False))