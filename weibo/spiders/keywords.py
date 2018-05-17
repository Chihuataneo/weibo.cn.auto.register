# -*- coding: utf-8 -*-
from weibo.common import *
from weibo.items import WeiboItem, CommentItem, TransItem

class KeyWordsSpider(scrapy.Spider):
    name = 'key'
    custom_settings = {'ITEM_PIPELINES': {'weibo.pipelines.KeywordsPipeline': 300}}
    tags = [
        'streetLA',
    ]
    key_url = 'https://weibo.cn/search/mblog?hideSearchFrame=&keyword=%s&page=%s'

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
                    # "username": "weibopachong@sina.com",
                    # "password": "weiboceshi",
                    "username": "13962775359",
                    "password": "wanghang1990",
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
                callback=self.generate_url
            )

    def generate_url(self, response):
        if not response.body:
            return
        tag = response.meta['tag']
        if tag:
            keys = tag.split(' ')
            word = '+'.join(keys)

        selector = Selector(response)
        if len(selector.xpath('//div[@class="pa"]')) > 0:
            weibo_page_text = selector.xpath('//div[@class="pa"]/form[1]/div[1]/text()').extract()[-1]
            weibo_page_account = int(re.findall('/([0-9]+)页', weibo_page_text)[0])
        else:
            weibo_page_account = 1
        for weibo_page in range(1, weibo_page_account + 1):
            url = KeyWordsSpider.key_url % (word, str(weibo_page))
            yield Request(
                url=url,
                meta={'tag': tag},
                headers=self.header,
                callback=self.parse_weibo
            )

    def parse_weibo(self, response):
        if not response.body:
            return
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
                        comment_href = ''
                        trans_href = ''
                        for a in divs[-1].xpath('./a'):
                            if len(a.xpath('./text()').extract()) < 1:
                                continue
                            if u'赞' in a.xpath('./text()').extract()[0]:
                                weibo_item['support_number'] = re.findall('([0-9]+)', a.xpath('./text()').extract()[0])[0]
                            if u'转发' in a.xpath('./text()').extract()[0]:
                                weibo_item['transpond_number'] = re.findall('([0-9]+)', a.xpath('./text()').extract()[0])[0]
                                trans_href = a.xpath('./@href').extract()[0]
                            if u'评论' in a.xpath('./text()').extract()[0]:
                                weibo_item['comment_number'] = re.findall('([0-9]+)', a.xpath('./text()').extract()[0])[0]
                                comment_href = a.xpath('./@href').extract()[0]
                        weibo_item['date'] = divs[-1].xpath('./span[@class="ct"]/text()').extract()[0]
                        if isCorrectTime(weibo_item['date']) == TOO_FORWARD_NEWS:
                            continue
                        elif (isCorrectTime(weibo_item['date']) == TOO_LATE_NEWS) and (u'上页' in selector.css('div.pa')[0].extract()):
                            return
                        weibo_item['tag'] = tag
                        yield weibo_item
                        comment_number = weibo_item['comment_number']
                        if comment_number.isdigit():
                            num_of_cpage = int(int(comment_number) / 10) + 1
                        else:
                            num_of_cpage = 1
                        trans_number = weibo_item['support_number']
                        if comment_number.isdigit():
                            num_of_tpage = int(int(trans_number) / 10) + 1
                        else:
                            num_of_tpage = 1

                        for page_number in range(1, num_of_cpage + 1):
                            yield Request(
                                url=comment_href.replace('#cmtfrm', '') + '&page=%s' % page_number,
                                meta={'tag': tag, 'content': weibo_item['content'], 'date': weibo_item['date']},
                                headers=self.header,
                                callback=self.parse_comment
                            )
                        for page_number in range(1, num_of_tpage + 1):
                            yield Request(
                                url=trans_href.replace('#cmtfrm', '') + '&page=%s' % page_number,
                                meta={'tag': tag, 'content': weibo_item['content'], 'date': weibo_item['date']},
                                headers=self.header,
                                callback=self.parse_trans
                            )

    def parse_comment(self, response):
        if not response.body:
            return
        weibo_content = response.meta['content']
        weibo_date = response.meta['date']
        observer_item = CommentItem()
        selector = Selector(response)
        observer_item['weibo_content'] = weibo_content
        observer_item['weibo_date'] = weibo_date
        observer_item['tag'] = response.meta['tag']
        comment_records = selector.xpath('//div[@class="c"]')

        for comment_record in comment_records[3:-1]:
            if comment_record:
                try:
                    observer_item['user'] = comment_record.xpath('./a[1]/text()').extract()[0]
                except Exception as e:
                    info = __file__ + ' line:' + str(sys._getframe().f_lineno)
                    log_err(e, info)
                    continue
                if u"查看更多热门" in observer_item['user']:
                    continue
                try:
                    observer_item['content'] = re.findall('<span class="ctt">(.+)</span>', comment_record.xpath('./span[@class="ctt"]').extract()[0])[0]
                except Exception as e:
                    observer_item['content'] = ''
                    info = __file__ + ' line:' + str(sys._getframe().f_lineno)
                    log_err(e, info)
                user_url = 'https://weibo.cn' + comment_record.xpath('./a[1]/@href').extract()[0]
                observer_item['user_url'] = user_url
                yield observer_item

    def parse_trans(self, response):
        if not response.body:
            return
        meta = response.meta
        selector = Selector(response)
        cs = selector.css('div.c')
        for c in cs:
            if len(c.xpath('./span[@class="cc"]')) and len(c.xpath('./span[@class="ct"]')):
                trans_item = TransItem()
                user_href = 'https://weibo.cn' + c.xpath('./a[1]/@href').extract()[0]
                trans_item['user'] = c.xpath('./a[1]/text()').extract()[0]
                trans_item['user_url'] = user_href
                trans_item['content'] = c.xpath('./text()').extract()[0]
                trans_item['weibo_content'] = meta['content']
                trans_item['weibo_date'] = meta['date']
                trans_item['support_number'] = re.findall('([0-9]+)', c.xpath('./span[@class="cc"]/a[1]/text()').extract()[0])[0]
                trans_item['tag'] = meta['tag']
                yield trans_item

    # def filter_weibo(self, response):
    #     if not response.body:
    #         return
    #     tag = response.meta['tag'] + '_' + 'Trans'
    #     content = response.meta['content']
    #     selector = Selector(response)
    #     weibos = selector.css('div.c')
    #     flag = 0
    #     if len(weibos) > 0:
    #         for weibo in weibos:
    #             if len(weibo.xpath('./@id')) > 0:
    #                 if content in weibo.extract():
    #                     divs = weibo.xpath('./div')
    #                     weibo_item = WeiboItem()
    #                     weibo_item['user_url'] = divs[1].xpath('./a[1]/@href').extract()[0]
    #                     weibo_item['content'] = content
    #                     for a in divs[-1].xpath('./a'):
    #                         if len(a.xpath('./text()').extract()) < 1:
    #                             continue
    #                         if u'赞' in a.xpath('./text()').extract()[0]:
    #                             weibo_item['support_number'] = a.xpath('./text()').extract()[0]
    #                         if u'转发' in a.xpath('./text()').extract()[0]:
    #                             weibo_item['transpond_number'] = a.xpath('./text()').extract()[0]
    #                         if u'评论' in a.xpath('./text()').extract()[0]:
    #                             weibo_item['comment_number'] = a.xpath('./text()').extract()[0]
    #                     weibo_item['date'] = divs[-1].xpath('./span[@class="ct"]/text()').extract()[0]
    #                     weibo_item['tag'] = tag
    #                     flag = 1
    #                     break
    #     if flag == 0:
    #         if selector.xpath('//*[@id="pagelist"]/form/div/a/text()').extract()[0] == u'下页':
    #             next_href = selector.xpath('//*[@id="pagelist"]/form/div/a/@href').extract()[0]
    #             yield Request('https://weibo.cn' + next_href, meta=response.meta, callback=self.filter_weibo)
