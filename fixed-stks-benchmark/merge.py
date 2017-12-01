# -*- coding: utf-8 -*-
# @desc: 合并收益率数据到一张图
# @file: merge
# @author: ME
# @date: 2017/11/24
import glob
import os
import pandas as pd
import re
from tqdm import tqdm

from stkdata import TFRQAlphaDataBackend
from benchmark.core import build_bench, draw_up_ratios


def extract_tags_from_filename(filename):
    basename = os.path.basename(filename)
    # close_day_level-0_count-1_top_down-False_20170806-20171117_up_ratio.csv
    # high_day_level-0_count-1_top_down-False_20170806-20171117_up_ratio.csv
    tags = basename[:len(basename) - len("_20170806-20171117_up_ratio.csv")]
    chosen_price, period, level, count, top_or_down = \
        re.search("(.*)_(.*)_level-(.*)_count-(.*)_top_down-(.*)", tags).groups()
    return tags, chosen_price, period, level, count, top_or_down


def merge_and_draw(filenames):
    # bench_df = None
    start_date = 20170806
    end_date = 20171117
    data_proxy = TFRQAlphaDataBackend()
    merged_close_df = None
    merged_high_df = None

    bench_df = build_bench(data_proxy, start_date, end_date)
    bench_df["close_up_ratio"] = (bench_df["close"] - bench_df["pre_close"]) * 100 / bench_df["pre_close"]
    bench_df["high_up_ratio"] = (bench_df["high"] - bench_df["pre_close"]) * 100 / bench_df["pre_close"]

    for filename in tqdm(filenames):
        tags = extract_tags_from_filename(filename)
        single_df = pd.read_csv(filename, sep=',', index_col='date',
                          usecols=["date", "tf_index_mean_up_ratio"],
                          parse_dates=["date"])


        if tags[1] == "close":
            # Draws
            draw_up_ratios(single_df["tf_index_mean_up_ratio"],
                           bench_df["close_up_ratio"], tags, start_date, end_date)

            single_df.columns = [tags[0]]
            merged_close_df = pd.concat([merged_close_df, single_df], axis=1)
        elif tags[1] == "high":
            # Draws
            draw_up_ratios(single_df["tf_index_mean_up_ratio"],
                           bench_df["high_up_ratio"], tags, start_date, end_date)

            single_df.columns = [tags[0]]
            merged_high_df = pd.concat([merged_high_df, single_df], axis=1)

    merged_high_df = pd.concat([merged_high_df, bench_df["high_up_ratio"]], axis=1)
    merged_close_df = pd.concat([merged_close_df, bench_df["close_up_ratio"]], axis=1)
    return merged_high_df, merged_close_df


if __name__ == '__main__':
    finals = glob.glob("ratios/*_up_ratio.csv")
    merged_high_df, merged_close_df = merge_and_draw(filenames=finals)

    def summary(df, prefix):
        df.to_csv("{}_all_mean_up_ratio.csv".format(prefix))
        des = df.describe()
        des.T.sort_values(by="mean", ascending=False).to_csv("{}_summary.T.csv".format(prefix))
        des.to_csv("{}_summary.csv".format(prefix))

    summary(merged_high_df, "high")
    summary(merged_close_df, "close")


