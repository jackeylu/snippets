# -*- coding: utf-8 -*-
# @desc: 基于文件的股票池
# @file: rebalance
# @author: ME
# @date: 2017/11/23
import datetime
import numpy as np
import pandas as pd
from stkdata.data_helper import TFRQAlphaDataBackend


class Rebalancer(object):
    def __init__(self):
        self.scores = pd.read_csv("score.csv", sep=",",
                     usecols =[
                         "composite_score",
                         "sec_ucode",
                         "date",
                         "indu_num"],
                     dtype={
                         "composite_score":np.float32,
                         "sec_ucode": np.str,
                         "date": np.int,
                         "indu_num": np.int})

        __data_proxy__ = TFRQAlphaDataBackend()
        def market_dates(stk_code, day):
            return __data_proxy__.market_days_from_listed(stk_code, day)

        self.dates = self.scores.date.unique()
        self.__stocks_set__ = self.scores["sec_ucode"].unique()
        self.stocks_days_from_listed = {}

        for day in self.dates:
            for stk in self.__stocks_set__:
                if stk not in self.stocks_days_from_listed:
                    self.stocks_days_from_listed[stk] = {}
                self.stocks_days_from_listed[stk][day] = market_dates(stk, day)
        print("初始化完成上市交易日数")
        
    @staticmethod
    def pre_trading_date(day):   # 背后依赖的RQAlpha Data Proxy不支持浅拷贝，需要深拷贝或重新构建新对象
        return TFRQAlphaDataBackend().get_previous_trading_date(day)

    @staticmethod
    def data_proxy():
        return TFRQAlphaDataBackend()


def get_stocks(day, count, level, top_down, helper):
    pre_day = helper.pre_trading_date(day)
    if isinstance(pre_day, datetime.datetime):
        pre_day = pre_day.year*10000 + pre_day.month * 100 + pre_day.day
    if helper.dates.min() > pre_day:
        return []

    closest_day = helper.dates[(np.abs(helper.dates - pre_day)).argmin()]
    if closest_day != pre_day:
        return []  # 去掉无得分的情况，避免推荐了一些“未来”股票
    # 股票按照日期抽取，然后按得分逆序排序
    stocks = helper.scores.query("date == {}".format(pre_day)).sort_values(
        by="composite_score", ascending=False)
    # 去掉次新股（上市交易不足20日）
    def new_stocks_or_not(stk_code, pre_day):
        return helper.stocks_days_from_listed[stk_code][pre_day] >= 20
    stocks = stocks[stocks["sec_ucode"].apply(new_stocks_or_not, args=(pre_day,))]
    start = int(stocks.shape[0] * .1 * level)
    end = int(stocks.shape[0] * .1 * (level+1))

    if top_down:  # 从上往下取
        if (end - start) > count:
            end = start + count
        stocks = stocks[start:end]
    else:  # 从底部向上取
        if (end - start) > count:
            start = end - count
        stocks = stocks[start:end]
    return stocks[["sec_ucode", "composite_score"]].values
