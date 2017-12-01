# -*- coding: utf-8 -*-
# @desc: 
# @file: core
# @author: ME
# @date: 2017/11/30
import os
import gc
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from stkdata import get_int_date, TFRQAlphaDataBackend, \
    trading_dates, position_perform, fetch_market_price
from stocks_producer.rebalance import get_stocks

plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
plt.style.use('ggplot')


def build_bench(data_proxy, start, end):
    bench_df = pd.DataFrame(data=fetch_market_price(data_proxy,
                                                    '000001.XSHG',
                                                    start,
                                                    end))
    bench_df["datetime"] = bench_df["datetime"] // 1000000
    bench_df.columns = ["date",
                        "open",
                        "close",
                        "high",
                        "low",
                        "volume",
                        "turnover"]
    bench_df["date"] = pd.to_datetime(bench_df["date"].apply(lambda x: "{}".format(x)))
    bench_df.set_index(keys=["date"], inplace=True)
    bench_df["pre_close"] = bench_df["close"].shift()
    return bench_df


def draw_up_ratios(single_series, bench_series, tags, start, end):
    describe = single_series.describe()
    chosen_price, period, level, count, top_down  = tags[1:]
    prefix = tags[0]

    plt.figure()
    single_series.plot(legend="index-mean-up-ratio")
    bench_series.plot(legend="bench-up-ratio")
    plt.ylim((-12, 12))
    plt.ylabel("涨跌幅:%")
    plt.title("{chosen_price} 涨跌幅 mean:{mean}%/std:{std}% 调仓周期:{period},level {level}\n"
              "From {top_down}, 股票数:{count}, 日期范围:{start}-{end}".format(
                chosen_price=chosen_price,
                mean=np.round(describe["mean"], 2),
                std=np.round(describe["std"], 2),
                period=period,
                level=level,
                top_down= "Top" if top_down == 'True' else "Down",
                count=count,
                start=start,
                end=end))
    plt.savefig("figures/{}_{}_up_ratio.png".format(chosen_price, prefix))
    plt.close()

def choose_core(period, count, start, end, level, top_down,
                  rebalancer, bench_df):
    prefix = "{}_level-{}_count-{}_top_down-{}_{}-{}".format(
        period, level, count, top_down, start, end)
    print('Run task %s (pid %s)...' % (prefix, os.getpid()))

    if period is None or count is None or start is None or end is None:
        print("lack of parameters, see `--help`")
        return

    data_proxy = TFRQAlphaDataBackend()
    __trading_dates = trading_dates(data_proxy=data_proxy, start=start, end=end)
    positions = position_perform(period,
                                 __trading_dates,
                                 count,
                                 level,
                                 top_down,
                                 rebalancer,
                                 data_proxy,
                                 stocks_getter=get_stocks)
    df_positions = positions.to_df()
    del positions

    df_positions.to_csv("raw_result/{}_positions_raw.csv".format(prefix))
    # print(os.path.abspath("raw_result/{}_positions_raw.csv".format(prefix)))

    df_positions["date"] = pd.to_datetime(df_positions["date"].apply(lambda x: "{}".format(x)))
    # df_positions.set_index(keys=["date"])

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

    for chosen_price in ["high", "close"]:
        # 涨跌幅 %
        df_positions["up_ratio"] = (df_positions[chosen_price] - df_positions["pre_close"]) * 100 / df_positions["pre_close"]
        index_up_ratio_diff = df_positions[["date", "up_ratio"]].groupby(by=["date"]).mean()

        bench_df["up_ratio"] = (bench_df[chosen_price] - bench_df["pre_close"]) * 100 / bench_df["pre_close"]
        ff = pd.concat([
            index_up_ratio_diff,
            bench_df["up_ratio"]], axis=1)
        ff.columns = ["tf_index_mean_up_ratio",
                      "bench_up_ratio"]
        ff = ff.dropna(axis=0)
        ff.to_csv("figure/{}_{}_up_ratio.csv".format(chosen_price, prefix))
        del ff

    del df_positions
    count = gc.collect()
    print("Gc {}".format(count))
    return

