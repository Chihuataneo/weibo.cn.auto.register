# -*- coding: utf-8 -*-
from weibo.common import *
from weibo.items import WeiboItem, CommentItem, FanItem

class KeyWordsSpider(scrapy.Spider):
    name = 'key'
    custom_settings = {'ITEM_PIPELINES': {'weibo.pipelines.KeywordsPipeline': 300}}
    tags = [
        'streetLA',
    ]

    def __init__(self):
        self.sso_login_url = 'https://passport.weibo.cn/sso/login'
        self.weibo_url_list = [
            # 'https://weibo.cn/tinagao7828', 'https://weibo.cn/kimolee', 'https://weibo.cn/baoruoxi',
            # 'https://weibo.cn/u/1913392383', 'https://weibo.cn/meijias', 'https://weibo.cn/minapie',
            # 'https://weibo.cn/u/2794430491', 'https://weibo.cn/BVBorussiaDortmund09'
            'https://weibo.cn/liyifeng2007',
        ]
        self.header = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.4843.400 QQBrowser/9.7.13021.400',
            'Referer': 'https://passport.weibo.cn/signin/login?entry=mweibo&r=http%3A%2F%2Fm.weibo.cn'
        }

    def start_requests(self):
        return [
            FormRequest(
                self.sso_login_url,
                headers=self.header,
                method="POST",
                formdata={
                    # **********input your login info***********
                    "username": "weibopachong@sina.com",
                    "password": "weiboceshi",
                    # ******************************************
                    "savestate": "1",
                    "r": "http://m.weibo.cn",
                    "ec": "0",
                    "pagerefer": "https://m.weibo.cn/p/102803_ctg1_8999_-_ctg1_8999_home",
                    "entry": "mweibo",
                    "wentry": "",
                    "loginfrom": "",
                    "client_id": "",
                    "code": "",
                    "qq": "",
                    "mainpageflag": "1",
                    "hff": "",
                    "hfp": ""},
                callback=self.verify)]

    def verify(self, response):
        body = json.loads(response.body)
        passport_url = body['data']['crossdomainlist']['weibo.cn']
        yield scrapy.Request(
            passport_url,
            headers=self.header,
            callback=self.login
        )

    def login(self, response):
        for index, weibo_url in enumerate(self.weibo_url_list):
            yield scrapy.Request(
                weibo_url,
                meta={'index': index},
                headers=self.header,
                callback=self.search_key
            )

    def search_key(self, response):
        for key in self.tags:
            yield scrapy.FormRequest(
                url='https://weibo.cn/search/',
                method='POST',
                formdata=
                {
                    'keyword': key,
                    'smblog': u'搜微博'
                },
                headers=self.header,
                callback=self.parse_weibo
            )

    def parse_weibo(self, response):
        pass
