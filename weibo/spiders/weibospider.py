# -*- coding: utf-8 -*-
from weibo.common import *
from weibo.items import WeiboItem, CommentItem, FanItem

class WeiboSpider(scrapy.Spider):
    name = 'weibo'
    custom_settings = {'ITEM_PIPELINES': {'weibo.pipelines.WeiboPipeline': 300}}
    tags = [
        # '高靓Tina', '李小科-Kimo', '桃巫齐edie', '李糖', 'MeijiaS', '米娜', 'BULLSNINEONE', '多特蒙德足球俱乐部',
        u'李易峰',
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
                callback=self.parse_weibo
            )

    def parse_weibo(self, response):
        weibo_item = WeiboItem()
        index = response.meta['index']
        selector = Selector(response)
        wbs = selector.xpath("//div[@class='c']")

        weibo_item['user_url'] = response.url
        weibo_item['tag'] = WeiboSpider.tags[index]

        for i in range(len(wbs) - 2):
            flag = 0
            wb_text = wbs[i].extract()
            comment_href = ''
            divs = wbs[i].xpath('./div')
            weibo_item['content'] = re.findall('<span class="ctt">(.+)</span>', divs[0].xpath('./span[@class="ctt"]').extract()[0])[0]
            for key in FILTER_WORDS:
                if key in weibo_item['content']:
                    flag = 1
                    break
            if flag == 0:
                continue

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
            yield Request(comment_href, meta={'weibo': weibo_item['content'], 'tag': weibo_item['tag']}, callback=self.parse_comment)

        if selector.xpath('//*[@id="pagelist"]/form/div/a/text()').extract()[0] == u'下页':
            next_href = selector.xpath('//*[@id="pagelist"]/form/div/a/@href').extract()[0]
            yield Request('https://weibo.cn' + next_href, meta={'index': index}, callback=self.parse_weibo)

    def parse_comment(self, response):
        try:
            current_page_no = int(re.findall('page=([0-9]+)', response.url)[0])
        except:
            pass
        observer_item = CommentItem()
        selector = Selector(response)
        weibo_content = response.meta['weibo']
        observer_item['weibo_content'] = weibo_content
        observer_item['tag'] = response.meta['tag']

        comment_records = selector.xpath('//div[@class="c"]')
        for comment_record in comment_records[3:-1]:
            try:
                observer_item['user'] = comment_record.xpath('./a[1]/text()').extract()[0]
            except Exception as e:
                with open('error.log', 'a+') as f:
                    f.write(str(e))
                continue
            if u"查看更多热门" in observer_item['user']:
                continue
            try:
                observer_item['content'] = re.findall('<span class="ctt">(.+)</span>', comment_record.xpath('./span[@class="ctt"]').extract()[0])[0]
            except Exception:
                observer_item['content'] = ''

            user_url = 'https://weibo.cn' + comment_record.xpath('./a[1]/@href').extract()[0]
            observer_item['user_url'] = user_url
            yield observer_item
            # yield Request(user_url, meta={'url': user_url, 'weibo': weibo_content, 'tag': observer_item['tag']}, callback=self.parse_user)

        try:
            if selector.xpath('//div[@id="pagelist"]/form/div/a/text()').extract()[0] == u'下页':
                next_href = 'https://weibo.cn' + selector.xpath('//*[@id="pagelist"]/form/div/a/@href').extract()[0]
                try:
                    with open('error.log', 'a+') as f:
                        f.write(next_href)
                    yield Request(next_href, meta={'weibo': weibo_content, 'tag': observer_item['tag']}, callback=self.parse_comment)
                except Exception as e:
                    with open('error.log', 'a+') as f:
                        f.write(str(e))
        except Exception as e:
            print(selector.xpath('//div[@id="pagelist"]').extract())
            with open('error.log', 'a+') as f:
                f.write(str(e))
            next_page = 'https://weibo.cn/comment/G09VUuIAg?uid=1291477752&rl=0&page=' + str(current_page_no + 2)
            with open('error.log', 'a+') as f:
                f.write(next_page)
            yield Request(next_page, meta={'weibo': weibo_content, 'tag': observer_item['tag']},
                          callback=self.parse_comment)

    def parse_user(self, response):
        user_item = FanItem()
        user_url = response.meta['url']
        weibo_content = response.meta['weibo']
        selector = Selector(response)
        user_info = selector.xpath('//div[@class="u"]')[0]
        user_item['user_url'] = user_url
        user_item['tag'] = response.meta['tag']
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
