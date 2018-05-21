# -*- coding: utf-8 -*-
from weibo.common import *
from weibo.items import WeiboItem, CommentItem, TransItem, SecLevelWeiboItem

class KeyWordsSpider(scrapy.Spider):
    name = 'key'
    WriteSwitch = True
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/53.0.2785.104 Safari/537.36 Core/1.53.4843.400 QQBrowser/9.7.13021.400',
            'Referer': 'https://passport.weibo.cn/signin/login?entry=mweibo&r=http%3A%2F%2Fm.weibo.cn'
        }
        self.ids = []
        self.zombie_fans = []

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
                callback=self.verify_cn)]

    def verify_cn(self, response):
        body = json.loads(response.body)
        self.passport_url_cn = body['data']['crossdomainlist']['weibo.cn']
        self.passport_url_com = body['data']['crossdomainlist']['weibo.com']
        yield scrapy.Request(
            self.passport_url_cn,
            headers=self.header,
            callback=self.verify_com
        )

    def verify_com(self, response):
        yield scrapy.Request(
            self.passport_url_com,
            headers=self.header,
            callback=self.search_key
        )

    def search_key(self, response):
        for key in self.tags:
            yield FormRequest(
                url='https://weibo.cn/search/',
                method='POST',
                formdata={
                    'keyword': key,
                    'smblog': u'搜微博'
                },
                meta={'tag': 'key_' + key},
                headers=self.header,
                callback=self.parse
            )

    def parse(self, response):
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
                    weibo_id = weibo.xpath('./@id').extract()[0]
                    if weibo_id not in self.ids:
                        self.ids.append(weibo_id)
                        weibo_item = WeiboItem()
                        weibo_item['user_url'] = weibo.xpath('./div[1]/a[1]/@href').extract()[0]
                        weibo_item['content'] = re.findall('<span class="ctt">:(.+)</span>', weibo.xpath('./div[1]/span[@class="ctt"]').extract()[0])[0]
                        # 通过搜索连续汉字字符串，确定微博关键字
                        weibo_keys = ''.join(weibo.xpath('./div[1]/span[@class="ctt"]/text()').extract())
                        if len(re.findall('([\u4e00-\u9fa5]+)', weibo_keys)) > 0:
                            weibo_keys = re.findall('([\u4e00-\u9fa5]+)', weibo_keys)[0]
                        else:
                            weibo_keys = ''
                        divs = weibo.xpath('./div')
                        comment_href = ''
                        trans_href = ''
                        for a in divs[-1].xpath('./a'):
                            if len(a.xpath('./text()').extract()) < 1:
                                continue
                            if u'赞' in a.xpath('./text()').extract()[0]:
                                weibo_item['support_number'] = re.findall('([0-9]+)',
                                                                          a.xpath('./text()').extract()[0])[0]
                            if u'转发' in a.xpath('./text()').extract()[0]:
                                weibo_item['transpond_number'] = re.findall('([0-9]+)',
                                                                            a.xpath('./text()').extract()[0])[0]
                                trans_href = a.xpath('./@href').extract()[0]
                            if u'评论' in a.xpath('./text()').extract()[0]:
                                weibo_item['comment_number'] = re.findall('([0-9]+)',
                                                                          a.xpath('./text()').extract()[0])[0]
                                comment_href = a.xpath('./@href').extract()[0]
                        weibo_item['date'] = divs[-1].xpath('./span[@class="ct"]/text()').extract()[0]
                        if isCorrectTime(weibo_item['date']) == TOO_FORWARD_NEWS:
                            continue
                        elif (isCorrectTime(weibo_item['date']) == TOO_LATE_NEWS) \
                                and (u'上页' not in selector.css('div.pa')[0].extract()):
                            continue
                        elif (isCorrectTime(weibo_item['date']) == TOO_LATE_NEWS) and \
                                (u'上页' in selector.css('div.pa')[0].extract()):
                            return
                        weibo_item['tag'] = tag
                        if KeyWordsSpider.WriteSwitch:
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
                                meta={'tag': tag, 'content': weibo_item['content'],
                                      'date': weibo_item['date'], 'weibo_keys': weibo_keys},
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
                    observer_item['content'] = re.findall('<span class="ctt">(.+)</span>',
                                                          comment_record.xpath('./span[@class="ctt"]').extract()[0])[0]
                except Exception as e:
                    observer_item['content'] = ''
                    info = __file__ + ' line:' + str(sys._getframe().f_lineno)
                    log_err(e, info)
                user_url = 'https://weibo.cn' + comment_record.xpath('./a[1]/@href').extract()[0]
                observer_item['user_url'] = user_url
                if KeyWordsSpider.WriteSwitch:
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
                user_href_cn = 'https://weibo.cn' + c.xpath('./a[1]/@href').extract()[0]
                trans_item['user'] = c.xpath('./a[1]/text()').extract()[0]
                trans_item['user_url'] = user_href_cn
                trans_item['content'] = c.xpath('./text()').extract()
                comment_keys = ''.join(trans_item['content'])
                if len(re.findall('([\u4e00-\u9fa5]+)', comment_keys)) > 0:
                    comment_keys = re.findall('([\u4e00-\u9fa5]+)', comment_keys)[0]
                else:
                    comment_keys = u'转发微博'
                meta['comment_keys'] = comment_keys
                trans_item['weibo_content'] = meta['content']
                trans_item['weibo_date'] = meta['date']
                trans_item['support_number'] = re.findall('([0-9]+)',
                                                          c.xpath('./span[@class="cc"]/a[1]/text()').extract()[0])[0]
                trans_item['tag'] = meta['tag']
                if KeyWordsSpider.WriteSwitch:
                    yield trans_item
                # parse next trans
                user_com_href = 'https://weibo.com' + c.xpath('./a[1]/@href').extract()[0]
                if user_com_href not in self.zombie_fans:
                    meta['user_com_href'] = user_com_href
                    yield Request(
                        url=user_com_href,
                        meta=meta,
                        headers=self.header,
                        callback=self.get_div_id
                    )

    def get_div_id(self, response):
        div_id = re.search('(Pl_Official_MyProfileFeed__[0-9]+)', response.body.decode()).group()
        if response.meta['weibo_keys'] == '' and response.meta['comment_keys'] == u'转发微博':
            return
        if response.meta['comment_keys'] == u'转发微博':
            keys = response.meta['weibo_keys']
        else:
            keys = response.meta['comment_keys']
        yield FormRequest(
            url=response.meta['user_com_href'],
            method='GET',
            formdata={
                'pids': div_id,
                'profile_ftype': '1',
                'is_all': '1',
                'is_search': '1',
                'key_word': keys,
                'ajaxpagelet': '1',
                'ajaxpagelet_v6': '1',
                '__ref': '/%s?profile_ftype=1&is_all=1#_0' %
                         re.findall('https://weibo.com/(.+)', response.meta['user_com_href'])[0],
                '_t': str(time.time()).replace('.', '')
            },
            meta=response.meta,
            headers=self.header,
            callback=self.parse_next_trans
        )

    def parse_next_trans(self, response):
        if not response.body:
            return
        body = response.body.decode()
        if u'找不到符合条件的微博，返回' in body:
            return
        else:
            body = re.findall('<script>parent.FM.view\((.+)\)</script>', body)[0]
            json_body = json.loads(body)['html']
            virtual_response = scrapy.http.TextResponse(url='', body=json_body.encode())
            selector = Selector(virtual_response)
            total = int(selector.css('div.WB_cardwrap.WB_result.S_bg1').
                        css('span.S_txt2').xpath('./em[1]/text()').extract()[0])

            if total > ZOBIE_FAN_CRITICAL_VALUE:
                self.zombie_fans.append(response.meta['user_com_href'])
                return
            else:
                slweibo_item = SecLevelWeiboItem()
                wbs = selector.css('div.WB_cardwrap.WB_feed_type.S_bg2.WB_feed_vipcover.WB_feed_like')
                if not len(wbs):
                    wbs = selector.css('div.WB_cardwrap.WB_feed_type.S_bg2.WB_feed_like')
                if not len(wbs):
                    return
                date = wbs[0].css('div.WB_feed_detail.clearfix').css('div.WB_detail').css('div.WB_from.S_txt2').xpath(
                    './a[1]/text()').extract()[0]
                target_divs = wbs[0].xpath('//div[@class="WB_feed_handle"]')
                if len(target_divs) > 0:
                    target_div = target_divs[0]
                    trans_info = target_div.xpath(
                        './div[1]/ul[1]/li[2]/a[1]/span[1]/span[1]/span[1]/em[2]/text()').extract()[0]
                    comment_info = target_div.xpath(
                        './div[1]/ul[1]/li[3]/a[1]/span[1]/span[1]/span[1]/em[2]/text()').extract()[0]
                    support_info = target_div.xpath(
                        './div[1]/ul[1]/li[4]/a[1]/span[1]/span[1]/span[1]/em[2]/text()').extract()[0]
                    if u'转发' in trans_info:
                        trans_num = 0
                    else:
                        trans_num = trans_info
                    if u'评论' in comment_info:
                        comment_num = 0
                    else:
                        comment_num = comment_info
                    if u'赞' in support_info:
                        support_num = 0
                    else:
                        support_num = support_info
                slweibo_item['user_url'] = response.meta['user_com_href']
                slweibo_item['content'] = response.meta['content']
                slweibo_item['support_number'] = support_num
                slweibo_item['transpond_number'] = trans_num
                slweibo_item['comment_number'] = comment_num
                slweibo_item['date'] = date
                slweibo_item['weibo_date'] = response.meta['date']
                slweibo_item['weibo_keys'] = response.meta['weibo_keys']
                slweibo_item['comment_keys'] = response.meta['comment_keys']
                slweibo_item['tag'] = response.meta['tag']
                if KeyWordsSpider.WriteSwitch:
                    yield slweibo_item
