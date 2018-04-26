# -*- coding: utf-8 -*-
from weibo.common import *


class TopicSpider(scrapy.Spider):
    name = 'topic'

    def __init__(self):
        self.sso_login_url = 'https://passport.weibo.cn/sso/login'
        self.weibo_url_list = ['https://weibo.com/p/1008082bb04e0912c994bdf91da2da21b0b411?k=%E6%96%AF%E5%87%AF%E5%A5%87%E5%85%A8%E6%B0%91battle%E5%AD%A3&_from_=huati_thread']
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
        for weibo_url in self.weibo_url_list:
            yield scrapy.Request(
                weibo_url,
                headers=self.header,
                callback=self.parse_topic
            )

    def parse_topic(self, response):
        print(6666666, response.body.decode('utf-8'))
        # with open('test.txt', 'w', encoding='utf-8') as f:
        #     f.write(json.dumps(response.body.decode('utf-8'), ensure_ascii=False))



        # selector = Selector(response)
        # topics = selector.xpath("//div[@class='WB_cardwrap.WB_feed_type.S_bg2.WB_feed_like']")
        # topics = selector.xpath("//*[@id='Pl_Core_StuffHeader__1']/div/div[2]/div")
        # print(6666666666666666)
        # print(len(topics))
        # for topic in topics:
        #     print(topic.extrac())
