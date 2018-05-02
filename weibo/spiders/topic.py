# -*- coding: utf-8 -*-
from weibo.common import *


class TopicSpider(scrapy.Spider):
    name = 'topic'

    def __init__(self):
        self.sso_login_url = 'https://passport.weibo.cn/sso/login'
        self.topic_url_list = ['https://weibo.com/p/1008082bb04e0912c994bdf91da2da21b0b411?feed_sort=white&feed_filter=white#Pl_Third_App__11']
        # ***********************url arg declare**************************
        # pagebar: roll times(value: 0 - n)
        # current_page: ..(value: 1 - n)
        # last_since_id: last page id
        # next_since_id: next page id
        # __rnd: time stamp
        self.comment_ajax_url = 'https://weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain=100808&feed_sort=white&feed_filter=white&pagebar=%s&tab=home&current_page=%s&since_id=%7B%22last_since_id%22%3A%s%2C%22res_type%22%3A1%2C%22next_since_id%22%3A%s%7D&pl_name=Pl_Third_App__11&id=1008082bb04e0912c994bdf91da2da21b0b411&script_uri=/p/1008082bb04e0912c994bdf91da2da21b0b411&feed_type=1&page=1&pre_page=1&domain_op=100808&__rnd=%s'
        # ****************************************************************
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
        passport_url = body['data']['crossdomainlist']['weibo.com']
        yield scrapy.Request(
            passport_url,
            headers=self.header,
            callback=self.login
        )

    def login(self, response):
        for topic_url in self.topic_url_list:
            yield scrapy.Request(
                topic_url,
                meta={'chrome': True},
                headers=self.header,
                callback=self.parse_topic
            )

    def parse_topic(self, response):
        selector = Selector(response)
        # print(response.body.decode())
        with open('test.txt', 'w', encoding='utf-8') as f:
            f.write(json.dumps(response.body.decode(), ensure_ascii=False))

        # yield scrapy.Request(
        #     headers=self.header,
        #     callback=self.parse_topic2
        # )

    def parse_topic2(self, response):
        with open('test2.txt', 'w', encoding='utf-8') as f:
            f.write(json.dumps(response.body.decode('unicode_escape'), ensure_ascii=False))
