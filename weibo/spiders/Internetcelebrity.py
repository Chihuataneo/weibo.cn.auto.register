# -*- coding: utf-8 -*-
from weibo.common import *
from weibo.items import WeiboItem, CommentItem, FanItem, TransItem, SecLevelWeiboItem

class ICSpider(scrapy.Spider):
    name = 'ic'
    WriteSwitch = True
    custom_settings = {'ITEM_PIPELINES': {'weibo.pipelines.WeiboPipeline': 300}}
    tags = [
        '高靓Tina',
        # '李小科-Kimo', '桃巫齐edie', '李糖', 'MeijiaS', '米娜', 'BULLSNINEONE', '多特蒙德足球俱乐部',
        # u'李易峰',
    ]
    weibo_url_list = [
        'https://weibo.cn/tinagao7828?',
        # 'https://weibo.cn/kimolee?', 'https://weibo.cn/baoruoxi?',
        # 'https://weibo.cn/u/1913392383?', 'https://weibo.cn/meijias?', 'https://weibo.cn/minapie?',
        # 'https://weibo.cn/u/2794430491?', 'https://weibo.cn/BVBorussiaDortmund09?'
        # 'https://weibo.cn/liyifeng2007?',
    ]

    def __init__(self):
        self.end_flag = 0
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
            callback=self.login
        )

    def login(self, response):
        for index, weibo_url in enumerate(ICSpider.weibo_url_list):
            yield scrapy.Request(
                weibo_url,
                meta={'index': index},
                headers=self.header,
                callback=self.parse
            )

    def parse(self, response):
        if not response.body:
            return
        star_url = response.url
        selector = Selector(response)
        if len(selector.xpath('//div[@class="pa"]')) > 0:
            weibo_page_text = selector.xpath('//div[@class="pa"]/form[1]/div[1]/text()').extract()[-1]
            weibo_page_account = int(re.findall('/([0-9]+)页', weibo_page_text)[0])
        else:
            weibo_page_account = 1
        meta = response.meta
        meta['weibo_page_account'] = weibo_page_account
        meta['next_page'] = 2
        meta['base_url'] = star_url + '?&page=%s'
        url = star_url + '?&page=1'
        yield Request(
            url=url,
            meta=meta,
            headers=self.header,
            callback=self.parse_weibo
        )

    def parse_weibo(self, response):
        if not response.body:
            return
        index = response.meta['index']
        next_page = response.meta['next_page']
        base_url = response.meta['base_url']
        weibo_page_account = response.meta['weibo_page_account']
        selector = Selector(response)
        wbs = selector.xpath("//div[@class='c']")
        weibo_item = WeiboItem()
        weibo_item['user_url'] = response.url
        weibo_item['tag'] = ICSpider.tags[index]

        if len(wbs) > 0:
            for wb in wbs:
                if len(wb.xpath('./@id')) > 0:
                    flag = 0
                    wb_text = wb.extract()
                    comment_href = ''
                    trans_href = ''
                    divs = wb.xpath('./div')
                    weibo_item['content'] = re.findall('<span class="ctt">(.+)</span>',
                                                       divs[0].xpath('./span[@class="ctt"]').extract()[0])[0]
                    # 通过搜索连续汉字字符串，确定微博关键字
                    weibo_keys = ''.join(wb.xpath('./div[1]/span[@class="ctt"]/text()').extract())
                    if len(re.findall('([\u4e00-\u9fa5]+)', weibo_keys)) > 0:
                        weibo_keys = re.findall('([\u4e00-\u9fa5]+)', weibo_keys)[0]
                    else:
                        weibo_keys = ''

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
                            trans_href = a[-3].xpath('./@href').extract()[0]
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
                            trans_href = a[-3].xpath('./@href').extract()[0]
                    yield weibo_item

                    comment_number = re.findall('([0-9]+)', weibo_item['comment_number'])[0]
                    if comment_number.isdigit():
                        num_of_cpage = int(int(comment_number)/10) + 1
                    else:
                        num_of_cpage = 1
                    for page_number in range(1, num_of_cpage + 1):
                        yield Request(comment_href.replace('#cmtfrm', '') + '&page=%s' % page_number,
                                      meta={'weibo': weibo_item['content'], 'tag': weibo_item['tag'],
                                            'date': weibo_item['date']},
                                      callback=self.parse_comment)

                    trans_number = re.findall('([0-9]+)', weibo_item['transpond_number'])[0]
                    if trans_number.isdigit():
                        num_of_tpage = int(int(trans_number) / 10) + 1
                    else:
                        num_of_tpage = 1
                    for page_number in range(1, num_of_tpage + 1):
                        yield Request(trans_href.replace('#cmtfrm', '') + '&page=%s' % page_number,
                                      meta={'tag': weibo_item['tag'], 'content': weibo_item['content'],
                                      'date': weibo_item['date'], 'weibo_keys': weibo_keys},
                                      callback=self.parse_trans)

        if next_page <= weibo_page_account:
            meta = response.meta
            meta['next_page'] += 1
            yield Request(
                url=base_url % str(next_page),
                meta=meta,
                headers=self.header,
                callback=self.parse_weibo
            )

    def parse_comment(self, response):
        observer_item = CommentItem()
        selector = Selector(response)
        weibo_content = response.meta['weibo']
        observer_item['weibo_content'] = weibo_content
        observer_item['tag'] = response.meta['tag']
        observer_item['weibo_date'] = response.meta['date']
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
                observer_item['content'] = re.findall('<span class="ctt">(.+)</span>',
                                                      comment_record.xpath('./span[@class="ctt"]').extract()[0])[0]
            except Exception as e:
                observer_item['content'] = ''
                with open('error.log', 'a+') as f:
                    f.write(str(e) + '\n')
            user_url = 'https://weibo.cn' + comment_record.xpath('./a[1]/@href').extract()[0]
            observer_item['user_url'] = user_url
            yield observer_item
            yield Request(user_url, meta={'url': user_url, 'weibo': weibo_content, 'tag': observer_item['tag']},
                          callback=self.parse_user)

    def parse_user(self, response):
        user_item = FanItem()
        user_url = response.meta['url']
        weibo_content = response.meta['weibo']
        selector = Selector(response)
        user_info = selector.xpath('//div[@class="u"]')[0]
        user_item['user_url'] = user_url
        user_item['tag'] = response.meta['tag']
        user_attrs = re.findall('.*([\u4e00-\u9fa5]+/[\u4e00-\u9fa5]+).*',
                                user_info.xpath('//span[@class="ctt"]').extract()[0])[0].split('/')
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
                if ICSpider.WriteSwitch:
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
            if len(response.meta['comment_keys']) > KEY_LEN:
                keys = response.meta['comment_keys']
            else:
                keys = response.meta['weibo_keys']
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
                if ICSpider.WriteSwitch:
                    yield slweibo_item
