# -*- coding: utf-8 -*-
from weibo.common import *
from weibo.items import TopicItem, WeiboItem

class TopicSpider(scrapy.Spider):
    name = 'topic'
    write_switch = False
    custom_settings = {'ITEM_PIPELINES': {'weibo.pipelines.TopicPipeline': 400}}

    def __init__(self):
        self.sso_login_url = 'https://passport.weibo.cn/sso/login'
        self.topic_url_list_by_reply_time = ['https://weibo.com/p/1008082bb04e0912c994bdf91da2da21b0b411?feed_sort=timeline&feed_filter=timeline#Pl_Third_App__11']
        self.topic_url_list_by_release_time = ['https://weibo.com/p/1008082bb04e0912c994bdf91da2da21b0b411?feed_sort=white&feed_filter=white#Pl_Third_App__11']
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
        for index, topic_url in enumerate(self.topic_url_list_by_reply_time):
            yield scrapy.Request(
                topic_url,
                meta={'index': index},
                headers=self.header,
                callback=self.parse_info
            )

    def parse_info(self, response):
        topic_item = TopicItem()
        index = response.meta['index']
        response_body = response.body.decode()
        scripts = re.findall('<script>(.+)</script>', response_body)
        for script in scripts:
            # browse every script,choose someone which is available
            if (u'阅读' in script) and (u'讨论' in script) and (u'粉丝' in script):
                topic_info = re.findall('FM.view\((.+)\)', script)[0]
                topic_dict = json.loads(topic_info)
                infos = re.findall('<strong class="">(.+)</strong>', topic_dict['html'])
                if len(infos) == INFO_LEN:
                    topic_item['read_times'] = infos[0]
                    topic_item['discuss_times'] = infos[0]
                    topic_item['fans_number'] = infos[0]
                    break
        if TopicSpider.write_switch:
            yield topic_item
        yield scrapy.Request(
            self.topic_url_list_by_release_time[index],
            headers=self.header,
            callback=self.parse_topic
        )

    def parse_topic(self, response):
        response_body = response.body.decode()
        scripts = re.findall('<script>(.+)</script>', response_body)
        for script in scripts:
            # browse every script,choose someone which is available
            if u'发布时间排序' in script:
                topic_content = re.findall('FM.view\((.+)}\)', script)[0] + '}'
                topic_dict = json.loads(topic_content)
                virtual_rep = scrapy.http.TextResponse(url='', body=topic_dict['html'].encode())
                virtual_rep._cached_ubody = topic_dict['html']
                selector = Selector(virtual_rep)

                wbs = selector.css("div.WB_cardwrap.WB_feed_type.S_bg2.WB_feed_like")
                for i, wb in enumerate(wbs):
                    topic_item = WeiboItem()
                    topic_item['user_url'] = wb.css('div.WB_feed_detail.clearfix').xpath('./div[@class="WB_detail"]/div[1]/a[1]/@href').extract()[0]
                    topic_item['date'] = wb.css('div.WB_feed_detail.clearfix').xpath('./div[@class="WB_detail"]/div[2]/a[1]/@title').extract()[0]
                    topic_item['content'] = wb.css('div.WB_feed_detail.clearfix').xpath('./div[@class="WB_detail"]').css('div.WB_text.W_f14').extract()[0]
                    topic_item['transpond_number'] = wb.xpath('./div[@class="WB_feed_handle"]/div[1]/ul[1]/li[2]/a[1]/span[1]/span[1]/span[1]/em[2]/text()').extract()[0]
                    topic_item['comment_number'] = wb.xpath('./div[@class="WB_feed_handle"]/div[1]/ul[1]/li[3]/a[1]/span[1]/span[1]/span[1]/em[2]/text()').extract()[0]
                    topic_item['support_number'] = wb.xpath('./div[@class="WB_feed_handle"]/div[1]/ul[1]/li[4]/a[1]/span[1]/span[1]/span[1]/em[2]/text()').extract()[0]
                    if TopicSpider.write_switch:
                        yield topic_item

                next_page = selector.css('div.WB_cardwrap.S_bg2').extract()[-1]
                with open('test.txt', 'w', encoding='utf-8') as f:
                    f.write(next_page)


    def parse_topic2(self, response):
        with open('test2.txt', 'w', encoding='utf-8') as f:
            f.write(json.dumps(response.body.decode('unicode_escape'), ensure_ascii=False))
