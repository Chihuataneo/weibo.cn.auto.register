# -*- coding: utf-8 -*-
from weibo.common import *
from weibo.items import WeiboItem, CommentItem, FanItem

class WeiboSpider(scrapy.Spider):
    name = 'weibo'

    def __init__(self):
        self.sso_login_url = 'https://passport.weibo.cn/sso/login'
        self.weibo_url_list = ['https://weibo.cn/BVBorussiaDortmund09?f=search_0']
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
        for weibo_url in self.weibo_url_list:
            yield scrapy.Request(
                weibo_url,
                headers=self.header,
                callback=self.parse_weibo
            )

    def parse_weibo(self, response):
        weibo_item = WeiboItem()
        selector = Selector(response)
        wbs = selector.xpath("//div[@class='c']")

        weibo_item['user_url'] = response.url

        for i in range(len(wbs) - 2):
            wb_text = wbs[i].extract()
            comment_href = ''
            divs = wbs[i].xpath('./div')
            weibo_item['content'] = re.findall('<span class="ctt">(.+)</span>', divs[0].xpath('./span[@class="ctt"]').extract()[0])[0]

            if len(divs) == 1:
                date = divs[0].xpath('./span[@class="ct"]/text()').extract()[0]
                if isCorrectTime(date) == TOO_FORWARD_NEWS:
                    continue
                elif (isCorrectTime(date) == TOO_LATE_NEWS) and (u'置顶' not in wb_text):
                    return
                weibo_item['date'] = date
                a = divs[0].xpath('./a')
                if len(a) > 0:
                    weibo_item['support_number'] = a[-4].xpath('./text()').extract()[0]
                    weibo_item['transpond_number'] = a[-3].xpath('./text()').extract()[0]
                    weibo_item['comment_number'] = a[-2].xpath('./text()').extract()[0]
                    comment_href = a[-2].xpath('./@href').extract()[0]
            if len(divs) > 1:
                date = divs[-1].xpath('./span[@class="ct"]/text()').extract()[0]
                if isCorrectTime(date) == TOO_FORWARD_NEWS:
                    continue
                elif (isCorrectTime(date) == TOO_LATE_NEWS) and (u'置顶' not in wb_text):
                    return
                weibo_item['date'] = date
                a = divs[1].xpath('./a')
                if len(a) > 0:
                    weibo_item['support_number'] = a[-4].xpath('./text()').extract()[0]
                    weibo_item['transpond_number'] = a[-3].xpath('./text()').extract()[0]
                    weibo_item['comment_number'] = a[-2].xpath('./text()').extract()[0]
                    comment_href = a[-2].xpath('./@href').extract()[0]
            yield weibo_item
            yield Request(comment_href, meta={'weibo': weibo_item['content']}, callback=self.parse_comment)

        if selector.xpath('//*[@id="pagelist"]/form/div/a/text()').extract()[0] == u'下页':
            next_href = selector.xpath('//*[@id="pagelist"]/form/div/a/@href').extract()[0]
            yield Request('https://weibo.cn' + next_href, callback=self.parse_weibo)

    def parse_comment(self, response):
        observer_item = CommentItem()
        selector = Selector(response)
        weibo_content = response.meta['weibo']
        observer_item['weibo_content'] = weibo_content

        comment_records = selector.xpath('//div[@class="c"]')
        for comment_record in comment_records[3:-1]:
            observer_item['user'] = comment_record.xpath('./a[1]/text()').extract()[0]
            if u"查看更多热门" in observer_item['user']:
                continue
            try:
                observer_item['content'] = re.findall('<span class="ctt">(.+)</span>', comment_record.xpath('./span[@class="ctt"]').extract()[0])[0]
            except Exception:
                observer_item['content'] = ''

            user_url = 'https://weibo.cn' + comment_record.xpath('./a[1]/@href').extract()[0]
            observer_item['user_url'] = user_url
            yield observer_item
            yield Request(user_url, meta={'url': user_url, 'weibo': weibo_content}, callback=self.parse_user)

        if selector.xpath('//*[@id="pagelist"]/form/div/a/text()').extract()[0] == u'下页':
            next_href = 'https://weibo.cn' + selector.xpath('//*[@id="pagelist"]/form/div/a/@href').extract()[0]
            # yield Request(next_href, meta={'item': weibo_item, 'weibo': weibo_content}, callback=self.parse_comment)
            yield Request(next_href, meta={'weibo': weibo_content}, callback=self.parse_comment)

    def parse_user(self, response):
        user_item = FanItem()
        user_url = response.meta['url']
        weibo_content = response.meta['weibo']
        selector = Selector(response)
        user_info = selector.xpath('//div[@class="u"]')[0]
        user_item['user_url'] = user_url
        user_attrs = re.findall('.*([\u4e00-\u9fa5]+/[\u4e00-\u9fa5]+).*', user_info.xpath('//span[@class="ctt"]').extract()[0])[0].split('/')
        user_item['sex'] = ''
        user_item['location'] = ''
        if len(user_attrs):
            if 1 == len(user_attrs):
                user_item['sex'] = user_attrs[0]
            elif 2 == len(user_attrs):
                user_item['sex'] = user_attrs[0]
                user_item['location'] = user_attrs[1]
        user_item['wbs'] = user_info.xpath('//div[@class="tip2"]/span[1]/text()').extract()[0]
        user_item['attent'] = user_info.xpath('//div[@class="tip2"]/a[1]/text()').extract()[0]
        user_item['fans'] = user_info.xpath('//div[@class="tip2"]/a[2]/text()').extract()[0]
        user_item['weibo_content'] = weibo_content
        yield user_item
