# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from weibo.common import *
from selenium import webdriver
from scrapy.http import HtmlResponse


class WeiboSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class WeiboDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ProxyMiddleware(object):
    def process_request(self, request, spider):
        request.meta['proxy'] = "http://http-dyn.abuyun.com:9020"
        proxy_user_pass = "H65M0VWE594O57LD:C866058A953A5629"
        encoded_user_pass = base64.b64encode(proxy_user_pass.encode(encoding='utf-8'))
        request.headers['Proxy-Authorization'] = 'Basic ' + encoded_user_pass.decode()


js = """
function scrollToBottom() {

    var Height = document.body.clientHeight,
        screenHeight = window.innerHeight,
        INTERVAL = 1000,
        delta = 500,
        curScrollTop = 0;

    var scroll = function () {
        curScrollTop = document.body.scrollTop;
        window.scrollTo(0,curScrollTop + delta);
    };

    var timer = setInterval(function () {
        var curHeight = curScrollTop + screenHeight;
        if (curHeight >= Height){
            clearInterval(timer);
        }
        scroll();
    }, INTERVAL)
}
scrollToBottom()
"""
class ChromeMiddleware(object):
    @classmethod
    def process_request(cls, request, spider):
        if 'chrome' in request.meta:
            # driver = webdriver.PhantomJS()
            # driver.get(request.url)
            # driver.execute_script(js)
            # time.sleep(3)
            # content = driver.page_source.encode('utf-8')
            # driver.quit()

            # /*******************headless chrome*******************/
            opt = webdriver.ChromeOptions()
            opt.set_headless()
            opt.add_argument('lang=zh_CN.UTF-8')
            opt.add_argument('user-agent="Mozilla/5.0 (iPod; U; CPU iPhone OS 2_1 like Mac OS X; ja-jp) AppleWebKit/525.18.1 (KHTML, like Gecko) Version/3.1.1 Mobile/5F137 Safari/525.20"')
            chromedriver = "C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe"
            driver = webdriver.Chrome(executable_path=chromedriver, options=opt)
            driver.get(request.url)
            time.sleep(3)
            driver.execute_script(js)
            time.sleep(3)
            content = driver.page_source
            driver.quit()
            return HtmlResponse(request.url, encoding='utf-8', body=content, request=request)
