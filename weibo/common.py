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

TIME_FILTER = 20180201

def isCorrectTime(time_para):
    try:
        if u'今天' in time_para:
            return True
        elif u'月' in time_para:
            date = int(time.strftime('%Y%m%d %H:%M:%S', time.localtime(time.time()))[:4] + time_para[0:2] + time_para[3:5])
            if date > TIME_FILTER:
                return True
            else:
                return False
        else:
            date = int(time_para[0:11].replace('-', ''))
            if date > TIME_FILTER:
                return True
            else:
                return False
    except Exception as e:
        print(e)
        return False
