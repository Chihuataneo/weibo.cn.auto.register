# -*- coding: utf-8 -*-
import os
import re
import sys
import json
import time
import scrapy
import base64
import requests
import chardet
from scrapy import signals
from scrapy import Selector
from scrapy.http import Request, FormRequest

# ----------------------------configuration space---------------------------#
TIME_FILTER_START = 20180518
TIME_FILTER_END = 20180601
FILTER_WORDS = [u'成都']
# ----------------------------configuration space---------------------------#

TOO_LATE_NEWS = 0
TOO_FORWARD_NEWS = 1
CORRECT_NEWS = 2

INFO_LEN = 3

ZOBIE_FAN_CRITICAL_VALUE = 10

KEY_LEN = 5


def isCorrectTime(time_para):
    try:
        if u'今天' in time_para or u'分钟前' in time_para:
            date = int(time.strftime('%Y%m%d %H:%M:%S', time.localtime(time.time()))[:-9])
            if date < TIME_FILTER_START:
                return TOO_LATE_NEWS
            elif date > TIME_FILTER_END:
                return TOO_FORWARD_NEWS
            else:
                return CORRECT_NEWS
        elif u'月' in time_para:
            date = int(time.strftime('%Y%m%d %H:%M:%S',
                                     time.localtime(time.time()))[:4] + time_para[0:2] + time_para[3:5])
            if date < TIME_FILTER_START:
                return TOO_LATE_NEWS
            elif date > TIME_FILTER_END:
                return TOO_FORWARD_NEWS
            else:
                return CORRECT_NEWS
        else:
            date = int(time_para[0:11].replace('-', ''))
            if date < TIME_FILTER_START:
                return TOO_LATE_NEWS
            elif date > TIME_FILTER_END:
                return TOO_FORWARD_NEWS
            else:
                return CORRECT_NEWS
    except Exception as e:
        print(e)
        return TOO_LATE_NEWS


def log_err(e, info):
    with open('error.log', 'a+') as f:
        f.write(str(e) + '\n')
        f.write(info + '\n\n')
