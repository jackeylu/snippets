# -*- coding: utf-8 -*-
# @desc: 
# @file: core
# @author: ME
# @date: 2017/11/30
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import stkdata
from stkdata.data_helper import get_int_date
from stocks_producer.rebalance import get_stocks

plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
plt.style.use('ggplot')


def choose_core(period, count, start, end, level, top_down,
                  rebalancer):
    prefix = "{}_level-{}_count-{}_top_down-{}_{}-{}".format(
        period, level, count, top_down, start, end)
    print('Run task %s (pid %s)...' % (prefix, os.getpid()))

    if period is None or count is None or start is None or end is None:
        print("lack of parameters, see `--help`")
        return

    trading_dates = stkdata.trading_dates(start, end)
    positions = stkdata.position_perform(period,
                                         trading_dates,
                                         count,
                                         level,
                                         top_down,
                                         rebalancer,
                                         stocks_getter=get_stocks)
    df_positions = positions.to_df()
    df_positions.to_csv("raw_result/{}_positions_raw.csv".format(prefix))
    # print(os.path.abspath("raw_result/{}_positions_raw.csv".format(prefix)))

    df_positions["date"] = pd.to_datetime(df_positions["date"].apply(lambda x: "{}".format(x)))
    # df_positions.set_index(keys=["date"])

    data_proxy = rebalancer.data_proxy()
    def get_pre_close_price(df):
        stock = df["stock"]
        __start = data_proxy.get_previous_trading_date(df["date"])
        __start = get_int_date(__start)
        try:
            pre_close = data_proxy.get_price(
                order_book_id=stock, start=__start, end=__start)["close"][0]
            return pre_close
        except KeyError:
            return None

    df_positions["pre_close"] = df_positions.apply(get_pre_close_price, axis=1)
    df_positions.to_csv("figure/{}_positions.csv".format(prefix))
    # print(os.path.abspath("figure/{}_positions.csv".format(prefix)))

    bench = pd.DataFrame(data=stkdata.fetch_market_price('000001.XSHG', start, end))
    bench["datetime"] = bench["datetime"] // 1000000
    bench.columns = ["date",
                     "open",
                     "close",
                     "high",
                     "low",
                     "volume",
                     "turnover"]
    bench["date"] = pd.to_datetime(bench["date"].apply(lambda x: "{}".format(x)))
    bench.set_index(keys=["date"], inplace=True)
    bench["pre_close"] = bench["close"].shift()

    for chosen_price in ["high", "close"]:
        # 涨跌幅 %
        df_positions["up_ratio"] = (df_positions[chosen_price] - df_positions["pre_close"]) * 100 / df_positions["pre_close"]
        index_up_ratio_diff = df_positions[["date", "up_ratio"]].groupby(by=["date"]).mean()

        bench["up_ratio"] = (bench[chosen_price] - bench["pre_close"]) * 100 / bench["pre_close"]
        ff = pd.concat([
            index_up_ratio_diff,
            bench["up_ratio"]], axis=1)
        ff.columns = ["tf_index_mean_up_ratio",
                      "bench_up_ratio"]
        ff = ff.dropna(axis=0)
        ff.to_csv("figure/{}_{}_up_ratio.csv".format(chosen_price, prefix))
        print("figure/{}_{}_up_ratio.csv".format(chosen_price, prefix))
        describe = ff["tf_index_mean_up_ratio"].describe()

        plt.figure()
        ff.tf_index_mean_up_ratio.plot(legend="index-mean-up-ratio")
        ff.bench_up_ratio.plot(legend="bench-up-ratio")
        plt.ylim((-12, 12))
        plt.ylabel("涨跌幅:%")
        plt.title("{} based 涨跌幅 mean:{}%/std:{}% 调仓周期: {}, level {} \n"
                  "top-down: {}, 股票数: {}, 日期范围: {}-{}".format(
                    chosen_price,
                    np.round(describe["mean"], 2),
                    np.round(describe["std"], 2),
                    period,
                    level,
                    top_down,
                    count,
                    start,
                    end))
        plt.savefig("figure/{}_{}_up_ratio.png".format(chosen_price, prefix))
        print("figure/{}_{}_up_ratio.png".format(chosen_price, prefix))
        plt.close()
    return

