# -*- coding: utf-8 -*-
# @desc: 取股票入选后的5日最高价
# @file: prices
# @author: ME
# @date: 2017/11/27
import numpy as np
import pandas as pd
from stkdata.data_helper import TFRQAlphaDataBackend, \
    get_int_date, stock_code_exchange, get_str_date_from_int

data_proxy = TFRQAlphaDataBackend()

df = pd.read_csv("stocks-data.csv",
                 encoding="gbk",
                 usecols=["组合ID",
                          "股票代码",
                          "市场",
                          "股票名",
                          "T日入选价", "T日期入选涨幅",
                          "T日最大涨幅",
                          "T日最高价",
                          "T日入选时间",
                          "现价",
                          "当日涨幅",
                          "最高价日期",
                          "10日最高涨幅",
                          "10日最高价",
                          "10日最高价日期",
                          "T+1日开盘价",
                          "T+1日",
                          "T+10日",
                          "T+1后最高涨幅"],
                 dtype={"股票代码":np.str},
                 parse_dates=["T日入选时间"])
                # engine="python")
print(df.dtypes)
# print(df.head(10))
df2 = df[["股票代码", "市场", "T日入选时间"]]


def T5_highest_price(df):
    stock_code = stock_code_exchange(df["股票代码"],df["市场"])
    start_day = data_proxy.get_next_trading_date(df["T日入选时间"])
    end_date = data_proxy.get_next_trading_date(start_day, n=5)
    bars = data_proxy.get_price(order_book_id=stock_code,
                                start=get_int_date(start_day),
                                end=get_int_date(end_date))
    idx = np.argmax(bars["high"])
    datetime = get_str_date_from_int(bars["datetime"][idx]//1000000)
    highest = bars["high"][idx]
    return pd.Series({"datetime": datetime, "highest": highest})

result = df2.apply(T5_highest_price, axis=1)
df["T+5中最高价日期"], df["T+5日最高价"] = result["datetime"], result["highest"]

df.to_csv("max-high.csv", encoding="gbk")
