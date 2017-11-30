# -*- coding: utf-8 -*-
# @desc: 
# @file: commands
# @author: ME
# @date: 2017/11/28


cmd = "python top-index.py --period {period} --start 20170801 " \
      "--end 20171117  --count {count} --level {level} --top_down {top_down}"

for period in ["day", "week", "month"]:
    for count in [1,2,3,4,5,6,10,15,20,30]:
        for level in range(10):
            for top_down in [True, False]:
                print(cmd.format(period=period, count=count,
                                 level=level, top_down=top_down))