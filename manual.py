# -*- coding: utf-8 -*-
# @desc: 手动执行一个实验
# @file: manual
# @author: ME
# @date: 2017/11/30
import click
import logging.config
from stocks_producer.rebalance import Rebalancer
from benchmark.core import choose_core


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
    return choose_core(period, count, start, end, level,
                         top_down, rebalancer)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
                        datefmt="%m-%d %H:%M")
    choose()