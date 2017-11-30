# -*- coding: utf-8 -*-
# @desc: TopN的股票价格变化指数
# @file: top-index
# @author: ME
# @date: 2017/11/23
import logging.config
import os
from multiprocessing import Pool

from stocks_producer.rebalance import Rebalancer
from benchmark.core import choose_core


def multi_run():
    logging.info('Parent process %s.' % os.getpid())
    rebalancer = Rebalancer()
    pool = Pool()
    for period in ["month", "week", "day"]:
        for count in [1, 2, 3, 4, 5, 6, 10, 15, 20, 30]:
            for level in range(10):
                for top_down in [True, False]:
                    pool.apply_async(choose_core, args=(
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
    multi_run()
