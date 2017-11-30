# -*- coding: utf-8 -*-
# @desc: TopN的股票价格变化指数
# @file: top-index
# @author: ME
# @date: 2017/11/23

import click
import logging.config
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

import numpy as np
import pandas as pd

import os
from multiprocessing import Pool

import stkdata
from stkdata.data_helper import TFRQAlphaDataBackend, get_int_date
from rebalance import Rebalancer, get_stocks

data_proxy = TFRQAlphaDataBackend()


@click.command()
@click.option('--period', default="month", type=click.Choice(["month", "week", "day"]),
              help="调仓周期，分为每月初、每周初、每交易日三种类型")
@click.option('--count', default=5, help='最大持仓个股数量.')
@click.option('--start', type=int, help='start day, like 20170501')
@click.option('--end', type=int, help='end day, like 20171123')
@click.option('--level', default=0, type=int, help='levels in {0,1,2,...,9}')
@click.option('--top_down', default=False,
              type=bool,
              help="股票池中取top count，还是逆序top count。默认逆序（按得分从高到低）")
def choose(period, count, start, end, level, top_down):
    rebalancer = Rebalancer()
    return __choose_core(period, count, start, end, level,
                         top_down, rebalancer)


def __choose_core(period, count, start, end, level, top_down,
                  rebalancer):
    prefix = "{}_level-{}_count-{}_top_down-{}_{}-{}".format(
        period, level, count, top_down, start, end)
    click.echo('Run task %s (%s)...' % (prefix, os.getpid()))

    if period is None or count is None or start is None or end is None:
        click.echo("lack of parameters, see `--help`")
        return


    trading_dates = stkdata.trading_dates(start, end)
    # click.echo("trading dates begin {} and end {}".format(trading_dates[0], trading_dates[-1]))
    positions = stkdata.position_perform(period,
                                         trading_dates,
                                         count,
                                         level,
                                         top_down,
                                         rebalancer,
                                         stocks_getter=get_stocks)
    # print(positions.toDf())
    df = positions.to_df()
    df.to_csv("raw_result/{}_positions_raw.csv".format(prefix))
    df["date"] = pd.to_datetime(df["date"].apply(lambda x: "{}".format(x)))
    df.set_index(keys=["date"])

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

    df["pre_close"] = df.apply(get_pre_close_price, axis=1)
    # df["pre_close"] = df.groupby(by="stock")["close"].shift()
    df.to_csv("figure/{}_positions.csv".format(prefix))

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
        df["up_ratio"] = (df[chosen_price] - df["pre_close"]) * 100 / df["pre_close"]
        index_up_ratio_diff = df[["date", "up_ratio"]].groupby(by=["date"]).mean()

        bench["up_ratio"] = (bench[chosen_price] - bench["pre_close"]) * 100 / bench["pre_close"]
        ff = pd.concat([
            index_up_ratio_diff,
            bench["up_ratio"]], axis=1)
        ff.columns = ["tf_index_mean_up_ratio",
                      "bench_up_ratio"]
        ff = ff.dropna(axis=0)
        ff.to_csv("figure/{}_{}_up_ratio.csv".format(chosen_price, prefix))
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
        plt.close()
    return


def multi_run():
    logging.info('Parent process %s.' % os.getpid())
    rebalancer = Rebalancer()
    pool = Pool(3)
    for period in ["month", "week", "day"]:
        for count in [1, 2, 3, 4, 5, 6, 10, 15, 20, 30]:
            for level in range(10):
                for top_down in [True, False]:
                    pool.apply_async(__choose_core, args=(
                        period,
                        count,
                        20170801,
                        20171117,
                        level,
                        top_down,
                        rebalancer
                    ))
    logging.info('Waiting for all subprocesses done...')
    pool.close()
    pool.join()
    logging.info('All subprocesses done.')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
                        datefmt="%m-%d %H:%M")

    #choose()
    multi_run()
