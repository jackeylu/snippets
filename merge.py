# -*- coding: utf-8 -*-
# @desc: 合并收益率数据到一张图
# @file: merge
# @author: ME
# @date: 2017/11/24
import glob
import os
import pandas as pd
from stkdata import TFRQAlphaDataBackend, fetch_market_price


def extract_tags_from_filename(filename):
    basename = os.path.basename(filename)
    # final_Period-day_count-1_level-0_ascending-False_start-20170801_end-20171117.csv
    return basename[len("final_"):len(basename) - len("_start-20170801_end-20171117.csv")]


def merge(filenames):
    # bench_df = None
    data_proxy = TFRQAlphaDataBackend()
    df = None
    for filename in filenames:
        tag = extract_tags_from_filename(filename)
        df1 = pd.read_csv(filename, sep=',', index_col='date',
                          usecols=["date", "tf_index_mean_up_ratio"],
                          parse_dates=["date"])
        df1.columns = [tag]
        df = pd.concat([df, df1], axis=1)

    bench = pd.DataFrame(data=fetch_market_price(data_proxy, '000001.XSHG', 20170807, 20171117))
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
    bench["up_ratio"] = (bench["close"] - bench["pre_close"]) * 100 / bench["pre_close"]
    df = pd.concat([df, bench["up_ratio"]], axis=1)
    return df


if __name__ == '__main__':
    finals = glob.glob("figure/final_*.csv")
    df = merge(filenames=finals)
    df.to_csv("all_mean_up_ratio.csv")
    df.describe().T.sort_values(by="mean", ascending=False).to_csv("describes.T.csv")
    df.describe().to_csv("describes.csv")
