
from datetime import date, timedelta

today = date.today()
cutoff = today - timedelta(days=365)

tests = {
    "国际原油": fetch_brent_history(),
    "国内汽油": fetch_oil95_history(),
    "国际黄金": fetch_gold_history_intl(),
    "国内黄金": fetch_gold_history_domestic(),
    "美国5年期国债": fetch_us_bond_history(),
    "基金481017": fetch_fund_history("481017"),
}

for name, data in tests.items():
    print("\n", "=" * 45)
    print(name)

    if not data:
        print("没有获取到数据")
        continue

    dates = [date.fromisoformat(x["date"]) for x in data]

    print("数据条数：", len(data))
    print("最早日期：", min(dates))
    print("最新日期：", max(dates))
    print("是否在最近一年：", min(dates) >= cutoff)
    print("是否日期升序：", dates == sorted(dates))
