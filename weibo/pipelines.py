# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from weibo.items import *


class WeiboPipeline(object):
    def process_item(self, item, spider):
        tag = item['tag']

        if isinstance(item, WeiboItem):
            self.f = open('result/' + tag + '_weibo_result.txt', 'a+', encoding='utf-8')
            line = json.dumps(dict(item), ensure_ascii=False) + '\n'
            self.f.write(line)
        elif isinstance(item, FanItem):
            self.f = open('result/' + tag + '_fans_result.txt', 'a+', encoding='utf-8')
            line = json.dumps(dict(item), ensure_ascii=False) + '\n'
            self.f.write(line)
        elif isinstance(item, CommentItem):
            self.f = open('result/' + tag + '_comment_result.txt', 'a+', encoding='utf-8')
            line = json.dumps(dict(item), ensure_ascii=False) + '\n'
            self.f.write(line)
        return item

    def close_spider(self, spider):
        self.f.close()


class TopicPipeline(object):
    def process_item(self, item, spider):
        tag = item['tag']

        if isinstance(item, TopicItem):
            self.f = open('result/' + tag + '_topic_info.txt', 'a+', encoding='utf-8')
            line = json.dumps(dict(item), ensure_ascii=False) + '\n'
            self.f.write(line)
        elif isinstance(item, WeiboItem):
            self.f = open('result/' + tag + '_topic_weibo_result.txt', 'a+', encoding='utf-8')
            line = json.dumps(dict(item), ensure_ascii=False) + '\n'
            self.f.write(line)
        return item

    def close_spider(self, spider):
        self.f.close()


class KeywordsPipeline(object):
    pass
