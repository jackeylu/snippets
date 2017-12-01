# -*- coding: utf-8 -*-
# @desc: TopN的股票价格变化指数
# @file: top-index
# @author: ME
# @date: 2017/11/23
import click
import logging.config
import time
import os
from multiprocessing import Pool

from stocks_producer.rebalance import Rebalancer
from benchmark.core import choose_core, build_bench
from stkdata import TFRQAlphaDataBackend


def run(var1, var2):
    print("{}, {}".format(var1, var2))

@click.command()
@click.option('--count', default=5, help='最大持仓个股数量.')
def multi_run(count):
    start_time = time.time()
    logging.info('Parent process %s.' % os.getpid())
    logging.info("准备所涉及股票交易日信息")
    start = 20170806
    end = 20171117
    data_proxy = TFRQAlphaDataBackend()
    rebalancer = Rebalancer(data_proxy)
    bench_df = build_bench(data_proxy=data_proxy, start=start, end=end)
    logging.info("准备完备")
    pool = Pool(3)
    for period in ["month", "week", "day"]: # , "week", "day"
        for level in range(10):
            for top_down in [True, False]: # False
                pool.apply_async(choose_core, args=(
                    period,
                    count,
                    start,
                    end,
                    level,
                    top_down,
                    rebalancer,
                    bench_df
                ))
                # pool.apply_async(run, args=(period, rebalancer))
    logging.info('Waiting for all subprocesses done...')
    pool.close()
    pool.join()
    cost = time.time() - start_time
    logging.info('All subprocesses done. cost {} seconds'.format(int(cost)))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
                        datefmt="%m-%d %H:%M")
    multi_run()
