# -*- coding: utf-8 -*-
# @desc: 仓位信息管理
# @file: position
# @author: ME
# @date: 2017/11/23
import logging
import pandas as pd
import numpy as np
from .market_price import fetch_market_price, int2datetime


class Positions(object):
    def __init__(self):
        self.__history__ = []
        self.current_stocks_info = []

    def log(self, stock, rows):
        assert 1 == rows.size, rows
        row = list(rows.tolist()[0])
        row[0] = row[0] // 1000000  # 去掉末尾的6个0
        row.append(stock[0])  # 股票代码
        row.append(stock[1])  # 诊股得分
        self.__history__.append(row)

    def to_df(self):
        df = pd.DataFrame(data=self.__history__,
                          columns=["date",
                                   "open",
                                   "close",
                                   "high",
                                   "low",
                                   "volume",
                                   "turnover",
                                   "limit_up",
                                   "limit_down",
                                   "stock",
                                   "score"]
                          )
        return df


def need_rebalance(period, day, last_day):
    if isinstance(day, int):
        day = int2datetime(day)
    if isinstance(last_day, int):
        last_day = int2datetime(last_day)
    if "month" == period:
        return last_day.month != day.month
    elif "week" == period:
        return np.abs((day - last_day).days) >= 7
    else:  # daily rebalance
        return day != last_day


def rebalance(positions, new_stocks_info, day, data_proxy):
    current_stocks_info = positions.current_stocks_info
    positions.current_stocks_info.clear()
    if len(new_stocks_info) != 0:
        current_stocks_info = new_stocks_info
    else:
        pass
    # TODO fees on selling out?
    for stock in current_stocks_info:
        if isinstance(stock, str):
            stock_code = stock
            score = None
        elif isinstance(stock, np.ndarray):
            stock_code = stock[0]
            score = stock[1]
        else:
            raise ValueError("Unknown type ", stock)
        try:
            ndarray = fetch_market_price(data_proxy=data_proxy,
                                         stock_code=stock_code,
                                         start_int=day)
        except KeyError:
            continue   # 去掉未
        row = list(ndarray.tolist()[0])
        row[0] = row[0] // 1000000  # 去掉末尾的6个0
        if row[0] < day:
            continue  # 去掉停牌的股票
        positions.current_stocks_info.append(stock_code)
        positions.log([stock_code, score], ndarray)


def update_balance(positions, day, data_proxy):
    # day = datetime2int(day)
    for stock in positions.current_stocks_info:
        # FIXME ndarray[0] != day，比如`day`日停牌了，那么返回的就是之前的价格
        if data_proxy.is_suspended(stock, day):
            continue
        ndarray = fetch_market_price(data_proxy=data_proxy, stock_code=stock, start_int=day)
        positions.log([stock, None], ndarray)


def position_perform(period, trading_dates, count, level,
                     top_down, helper, data_proxy, stocks_getter):
    positions = Positions()
    last_rebalance_day = None
    for i, day in enumerate(trading_dates):
        if last_rebalance_day is None or len(positions.current_stocks_info) == 0\
                or need_rebalance(period, day, last_rebalance_day):
            logging.info("Rebalance on %s", day)
            new_stocks = stocks_getter(day, count, level,
                                       top_down, helper, data_proxy)
            rebalance(positions, new_stocks, day, data_proxy)
            last_rebalance_day = day
        else:
            update_balance(positions, day, data_proxy)

    return positions
