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
        self.header = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.4843.400 QQBrowser/9.7.13021.400',
            'Referer': 'https://passport.weibo.cn/signin/login?entry=mweibo&r=http%3A%2F%2Fm.weibo.cn'
        }
        self.ids = []

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
                meta={'tag': key},
                headers=self.header,
                callback=self.parse_weibo
            )

    def parse_weibo(self, response):
        tag = response.meta['tag']
        selector = Selector(response)
        weibos = selector.css('div.c')

        if len(weibos) > 0:
            for weibo in weibos:
                if len(weibo.xpath('./@id')) > 0:
                    id = weibo.xpath('./@id').extract()[0]
                    if id not in self.ids:
                        self.ids.append(id)
                        weibo_item = WeiboItem()
                        weibo_item['user_url'] = weibo.xpath('./div[1]/a[1]/@href').extract()[0]
                        weibo_item['content'] = weibo.xpath('./div[1]/span[@class="ctt"]').extract()[0]
                        divs = weibo.xpath('./div')
                        trans_href = ''
                        for a in divs[-1].xpath('./a'):
                            if len(a.xpath('./text()').extract()) < 1:
                                continue
                            if u'赞' in a.xpath('./text()').extract()[0]:
                                weibo_item['support_number'] = a.xpath('./text()').extract()[0]
                            if u'转发' in a.xpath('./text()').extract()[0]:
                                weibo_item['transpond_number'] = a.xpath('./text()').extract()[0]
                                trans_href = a.xpath('./@href').extract()[0]
                            if u'评论' in a.xpath('./text()').extract()[0]:
                                weibo_item['comment_number'] = a.xpath('./text()').extract()[0]
                        weibo_item['date'] = divs[-1].xpath('./span[@class="ct"]/text()').extract()[0]
                        weibo_item['tag'] = tag
                        # yield weibo_item
                        yield Request(
                            url=trans_href,
                            headers=self.header,
                            callback=self.parse_trans
                        )
        # try:
        #     page = selector.css('div.pa')[0]
        #     a_list = page.xpath('./form[1]/div[1]/a')
        #     for a in a_list:
        #         if u'下页' in a.xpath('./text()').extract()[0]:
        #             href = 'https://weibo.cn' + a.xpath('./@href').extract()[0]
        #             yield scrapy.Request(
        #                 url=href,
        #                 meta={'tag': tag},
        #                 headers=self.header,
        #                 callback=self.parse_weibo
        #             )
        # except Exception as e:
        #     print(e)

    def parse_trans(self, response):
        if not response.body:
            return

        selector = Selector(response)
        cs = selector.css('div.c')
        for c in cs:
            if len(c.xpath('./span[@class="cc"]')) and len(c.xpath('./span[@class="ct"]')):
                print(c.extract())





