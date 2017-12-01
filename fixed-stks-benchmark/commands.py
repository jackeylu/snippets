# -*- coding: utf-8 -*-
# @desc: 
# @file: commands
# @author: ME
# @date: 2017/11/28


cmd = "python batch-test.py --count {count}"

l = [1,2,3,4,5,6,10,15,20,30]
l.reverse()
for count in l:
    print(cmd.format(count=count))