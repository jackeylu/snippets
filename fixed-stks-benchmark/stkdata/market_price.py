# -*- coding: utf-8 -*-
# @desc: 
# @file: trading_dates
# @author: ME
# @date: 2017/11/23
import datetime
import json
import logging
import os
import numpy as np
import pandas as pd
import pickle
import requests

UNIX_EPOCH = np.datetime64('1970-01-01T00:00:00')
TIME_DELTA = np.timedelta64(1, 's')


def fetch_stock_price(stock_code, start_day,
                      value=["open", "close", "high", "low"],
                      delta=0):
    real_start_day = start_day
    enlarged_end_day = real_start_day
    if delta < 0:
        real_start_day = real_start_day + datetime.timedelta(delta * 10)
    else:
        enlarged_end_day = real_start_day + datetime.timedelta(delta * 10)

    real_start_day_int = datetime2int(real_start_day)
    enlarged_end_day_int = datetime2int(enlarged_end_day)
    _trading_dates = trading_dates(real_start_day_int, enlarged_end_day_int)
    dates = np.asarray([_ for _ in _trading_dates])
    day = dates[np.abs(_trading_dates - real_start_day).argmin() + np.abs(delta)]
    df = fetch_market_price(stock_code, real_start_day_int, enlarged_end_day_int)
    return df.query("date >= {} and date <= {}".format(
        real_start_day_int, datetime2int(day)))[value].values


def fetch_market_price(data_proxy, stock_code, start_int, end_int=None):
    if end_int is None:
        end_int = start_int
    return data_proxy.get_price(order_book_id=stock_code, start=start_int, end=end_int)

def fetch_market_price_from_thinkive(stock_code, start_int, end_int=None):
    assert isinstance(start_int, int)
    assert end_int is None or isinstance(end_int, int)

    now = datetime.datetime.now()
    if end_int is None or now < int2datetime(end_int):
        end_int = datetime2int(now) - 1

    days = (now - int2datetime(start_int)).days

    basic_dir = "data"
    bench_url = "http://183.57.43.58:10088/market/json?funcno=20002&version=1&stock_code={}&market={}&type=day&count={}"

    filename = "{}/{}.pickle".format(basic_dir, stock_code)
    if os.path.exists(filename):
        df = pickle.load(open(filename, "rb"))
        start_date, end_date = datetime2int(df.date[0]), datetime2int(df.date[df.shape[0]-1])
        if start_date <= start_int and end_int <= end_date:
            # FIXME 停牌的股票会每次都尝试取这个行情数据，会造成一定程度的重复覆写
            logging.debug("Reuse existed market price data {}".format(filename))
            return df.query("date >= {} and date <= {}".format(start_int, end_int))

    def code_and_exchange(stock_code):
        """002632.XSHE like"""
        code = stock_code[:6]
        exchange = stock_code[7:]
        if "XSHE" == exchange:
            return code, "SZ"
        else:
            return code, "SH"

    code, exchg = code_and_exchange(stock_code)
    url = bench_url.format(code, exchg, days)

    response = requests.get(url)
    assert response.ok, response
    values = json.loads(response.text, encoding=response.encoding)
    assert values["errorNo"] == 0, "url = {}\n {}".format(url, values["errorInfo"])
    df = pd.DataFrame(values["results"], columns=["date",
                                                  "open",
                                                  "high",
                                                  "close",
                                                  "low",
                                                  "vol",
                                                  "turnover"])
    df["date"] = df["date"].apply(lambda x: pd.to_datetime("%s" % x))

    if not os.path.exists(basic_dir):
        os.mkdir(basic_dir)
    pickle.dump(df, open(filename, mode='wb'))
    logging.info("Save market price to {} for reusing.".format(filename))
    return df.query("date >= {} and date <= {}".format(start_int, end_int))


def trading_dates(data_proxy, start, end):
    return data_proxy.get_trading_dates(start, end)


def int2datetime(int_day):
    year = int_day // 10000
    month = (int_day - year * 10000) // 100
    day = (int_day - year * 10000 - month * 100)
    return datetime.datetime(year=year, month=month, day=day)


def datetime2int(date):
    assert isinstance(date, datetime.datetime)
    return date.year * 10000 + date.month * 100 + date.day


def dt64_to_datetime(dt64):
    assert isinstance(dt64, np.datetime64) or \
           (isinstance(dt64, np.ndarray) and dt64.dtype.type is np.datetime64)
    return map(datetime.datetime.utcfromtimestamp,
               (dt64 - UNIX_EPOCH)/TIME_DELTA )


if __name__ == '__main__':
    date = int2datetime(20171101)
    r = fetch_stock_price("000001.XSHG", date, delta=5)
    print(r)