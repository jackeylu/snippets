# -*- coding: utf-8 -*-
# @desc: 从RQAlpha的离线bundle数据中加载数据
# @file: data_helper
# @author: ME
# @date: 2017/11/27
import datetime
import numpy as np
from funcat.data.rqalpha_data_backend import RQAlphaDataBackend


class TFRQAlphaDataBackend(RQAlphaDataBackend):
    def __init__(self, bundle_path="~/.rqalpha/bundle"):
        super().__init__(bundle_path)

    def get_price(self, order_book_id, start, end):
        """
        获取日K数据
        :param order_book_id: 000002.XSHE 这样的股票代码格式
        :param start: int 类型
        :param end: int 类型
        :return:
        """
        if end is None:
            end = get_int_date(start)
            # start = get_int_date(get_date_from_int(start) - datetime.timedelta(days=1))
        try:
            return super().get_price(order_book_id, start, end, freq="1d")
        except AttributeError as e:
            if e.args[0] == "'NoneType' object has no attribute 'type'":
                raise AttributeError(u"Invalid order: {}".format(order_book_id))
            else:
                raise e

    def get_next_trading_date(self, date, n=1):
        return self.data_proxy.get_next_trading_date(date=date, n=n)

    def get_previous_trading_date(self, date, n=1):
        if isinstance(date, int):
            date = get_date_from_int(date)
        return self.data_proxy.get_previous_trading_date(date=date, n=n)

    def is_suspended(self, stock_code, day):
        return self.data_proxy.is_suspended(stock_code, dt=day, count=1)

    def is_unlist(self, stock_code, day):
        """
        判断个股是否在该日已上市
        :param stock_code:
        :param day:
        :return:
        """
        try:
            self.get_price(stock_code, day, day)
            return False
        except KeyError:
            return True

    def get_listed_date(self, stock_code):
        """
        获得股票上市时间
        :param stock_code:
        :return:
        """
        instrument = self.data_proxy.instruments(stock_code)
        if instrument is None:
            raise KeyError('Invalid stock code, unable to find.', stock_code)
        return instrument.listed_date

    def market_days_from_listed(self, stock_code, day):
        """
        计算给定日期与上市时间的交易日差距
        :param stock_code:
        :param day:
        :return: 负数表示给定时间在上市时间之前
        """
        listed_date = self.get_listed_date(stock_code)
        if isinstance(day, (int, np.int64)):
            day = get_date_from_int(day)
        else:
            print(day)
        if day < listed_date:
            return -len(self.data_proxy.get_trading_dates(day, listed_date))
        else:
            return len(self.data_proxy.get_trading_dates(listed_date, day))



def get_int_date(date):
    """
    将时间转换成整数形式，例如
        "20171101" --> 20171101
        20171101 --> 20171101
        "2017-11-01" --> 20171101
    :param date:
    :return:
    """
    # 直接是整数，则直接返回
    if isinstance(date, int):
        return date

    # 两种时间格式
    try:
        return int(datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%Y%m%d"))
    except:
        pass

    try:
        return int(datetime.datetime.strptime(date, "%Y%m%d").strftime("%Y%m%d"))
    except:
        pass

    if isinstance(date, (datetime.date)):
        return int(date.strftime("%Y%m%d"))

    raise ValueError("unknown date {}".format(date))


def get_str_date_from_int(date_int):
    """
    将整数形式的时间转换成年月日格式的字符串 "2017-11-01"这样的
    :param date_int:
    :return:
    """
    try:
        date_int = int(date_int)
    except ValueError:
        date_int = int(date_int.replace("-", ""))
    year = date_int // 10000
    month = (date_int % 10000) // 100
    day = date_int % 100

    return "%d-%02d-%02d" % (year, month, day)


def get_date_from_int(date_int):
    """
    将一个整数形式的时间转换成`datetime.datetime`形式。
    :param date_int:
    :return:
    """
    date_str = get_str_date_from_int(date_int)

    return datetime.datetime.strptime(date_str, "%Y-%m-%d")


def stock_code_exchange(stock_code, exchange):
    """
    将股票代码和市场合并，生成业内习惯的唯一代码（股票指数也可以）
    :param stock_code:
    :param exchange:
    :return:
    """
    if "SH" == exchange:
        return "{}.{}".format(stock_code, "XSHG")
    else:
        return "{}.{}".format(stock_code, "XSHE")

