# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from weibo.items import *


class WeiboPipeline(object):
    # def __init__(self):
    #     if sys.version > '3':
    #         self.f = open('weibo_result.txt', 'a+', encoding='utf-8')
    #     else:
    #         self.f = open('weibo_result.txt', 'a+')

    def process_item(self, item, spider):
        if isinstance(item, WeiboItem):
            self.f = open('result/weibo_result.txt', 'a+', encoding='utf-8')
            line = json.dumps(dict(item), ensure_ascii=False) + '\n'
            self.f.write(line)
        if isinstance(item, FanItem):
            self.f = open('result/fans_result.txt', 'a+', encoding='utf-8')
            line = json.dumps(dict(item), ensure_ascii=False) + '\n'
            self.f.write(line)
        return item

    def close_spider(self, spider):
        self.f.close()
