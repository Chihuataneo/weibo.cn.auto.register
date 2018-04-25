# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
from weibo.common import *


class WeiboItem(scrapy.Item):
    # define the fields for your item here like:
    user_url = scrapy.Field()
    content = scrapy.Field()
    support_number = scrapy.Field()
    transpond_number = scrapy.Field()
    comment_number = scrapy.Field()
    date = scrapy.Field()
    # observer = scrapy.Field()


class CommentItem(scrapy.Item):
    user = scrapy.Field()
    user_url = scrapy.Field()
    content = scrapy.Field()
    weibo_content = scrapy.Field()


class FanItem(scrapy.Item):
    user_url = scrapy.Field()
    attent = scrapy.Field()
    fans = scrapy.Field()
    wbs = scrapy.Field()
    sex = scrapy.Field()
    location = scrapy.Field()
    weibo_content = scrapy.Field()
