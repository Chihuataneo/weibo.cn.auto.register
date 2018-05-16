# -*- coding: utf-8 -*-
from weibo.common import *
from weibo.items import WeiboItem, CommentItem, TransItem

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
                        comment_href = ''
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
                                comment_href = a.xpath('./@href').extract()[0]
                        weibo_item['date'] = divs[-1].xpath('./span[@class="ct"]/text()').extract()[0]
                        weibo_item['tag'] = tag
                        # yield weibo_item
                        comment_number = re.findall('([0-9]+)', weibo_item['comment_number'])[0]
                        if comment_number.isdigit():
                            num_of_cpage = int(int(comment_number) / 10) + 1
                        else:
                            num_of_cpage = 0
                        trans_number = re.findall('([0-9]+)', weibo_item['support_number'])[0]
                        if comment_number.isdigit():
                            num_of_tpage = int(int(trans_number) / 10) + 1
                        else:
                            num_of_tpage = 0
                        yield Request(
                            url=comment_href,
                            meta={'tag': tag, 'content': weibo_item['content'], 'page': num_of_cpage},
                            headers=self.header,
                            callback=self.parse_comment
                        )
                        yield Request(
                            url=trans_href,
                            meta={'tag': tag, 'content': weibo_item['content'], 'page': num_of_tpage},
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

    def parse_comment(self, response):
        if not response.body:
            return
        try:
            current_page_no = int(re.findall('page=([0-9]+)', response.url)[0])
        except:
            pass
        num_of_page = response.meta['page']
        observer_item = CommentItem()
        selector = Selector(response)
        weibo_content = response.meta['content']
        observer_item['weibo_content'] = weibo_content
        observer_item['tag'] = response.meta['tag']
        comment_records = selector.xpath('//div[@class="c"]')

        for comment_record in comment_records[3:-1]:
            try:
                observer_item['user'] = comment_record.xpath('./a[1]/text()').extract()[0]
            except Exception as e:
                with open('error.log', 'a+') as f:
                    f.write(str(e) + '\n')
                continue
            if u"查看更多热门" in observer_item['user']:
                continue
            try:
                observer_item['content'] = re.findall('<span class="ctt">(.+)</span>', comment_record.xpath('./span[@class="ctt"]').extract()[0])[0]
            except Exception as e:
                observer_item['content'] = ''
                with open('error.log', 'a+') as f:
                    f.write(str(e) + '\n')
            user_url = 'https://weibo.cn' + comment_record.xpath('./a[1]/@href').extract()[0]
            observer_item['user_url'] = user_url
            # yield observer_item
        try:
            if selector.xpath('//div[@id="pagelist"]/form/div/a/text()').extract()[0] == u'下页':
                next_href = 'https://weibo.cn' + selector.xpath('//*[@id="pagelist"]/form/div/a/@href').extract()[0]
                try:
                    yield Request(next_href, meta=response.meta, callback=self.parse_comment)
                except Exception as e:
                    with open('error.log', 'a+') as f:
                        f.write(str(e) + '\n')
        except Exception as e:
            if current_page_no >= num_of_page:
                return
            next_page = re.findall('(https.+&page=)', response.url)[0] + str(current_page_no + 2)
            yield Request(next_page, meta=response.meta, callback=self.parse_comment)

    def parse_trans(self, response):
        if not response.body:
            return
        try:
            current_page_no = int(re.findall('page=([0-9]+)', response.url)[0])
        except:
            pass
        num_of_page = response.meta['page']
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
                trans_item['support_number'] = c.xpath('./span[@class="cc"]/a[1]/text()').extract()[0]
                trans_item['tag'] = meta['tag']
                yield trans_item
        try:
            if selector.xpath('//div[@id="pagelist"]/form/div/a/text()').extract()[0] == u'下页':
                next_href = 'https://weibo.cn' + selector.xpath('//*[@id="pagelist"]/form/div/a/@href').extract()[0]
                try:
                    yield Request(next_href, meta=response.meta, callback=self.parse_trans)
                except Exception as e:
                    with open('error.log', 'a+') as f:
                        f.write(str(e) + '\n')
        except Exception as e:
            if current_page_no >= num_of_page:
                return
            next_page = next_page = re.findall('(https.+&page=)', response.url)[0] + str(current_page_no + 2)
            yield Request(next_page, meta=response.meta, callback=self.parse_trans)


    def filter_weibo(self, response):
        if not response.body:
            return
        tag = response.meta['tag'] + '_' + 'Trans'
        content = response.meta['content']
        selector = Selector(response)
        weibos = selector.css('div.c')
        flag = 0
        if len(weibos) > 0:
            for weibo in weibos:
                if len(weibo.xpath('./@id')) > 0:
                    if content in weibo.extract():
                        divs = weibo.xpath('./div')
                        weibo_item = WeiboItem()
                        weibo_item['user_url'] = divs[1].xpath('./a[1]/@href').extract()[0]
                        weibo_item['content'] = content
                        for a in divs[-1].xpath('./a'):
                            if len(a.xpath('./text()').extract()) < 1:
                                continue
                            if u'赞' in a.xpath('./text()').extract()[0]:
                                weibo_item['support_number'] = a.xpath('./text()').extract()[0]
                            if u'转发' in a.xpath('./text()').extract()[0]:
                                weibo_item['transpond_number'] = a.xpath('./text()').extract()[0]
                            if u'评论' in a.xpath('./text()').extract()[0]:
                                weibo_item['comment_number'] = a.xpath('./text()').extract()[0]
                        weibo_item['date'] = divs[-1].xpath('./span[@class="ct"]/text()').extract()[0]
                        weibo_item['tag'] = tag
                        flag = 1
                        print(weibo_item)
                        break
        if flag == 0:
            if selector.xpath('//*[@id="pagelist"]/form/div/a/text()').extract()[0] == u'下页':
                next_href = selector.xpath('//*[@id="pagelist"]/form/div/a/@href').extract()[0]
                yield Request('https://weibo.cn' + next_href, meta=response.meta, callback=self.filter_weibo)










