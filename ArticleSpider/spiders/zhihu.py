# -*- coding: utf-8 -*-
import scrapy
import os
import re
import time
import pickle
from selenium import webdriver
from urllib import parse
from ArticleSpider.items import ZhiHuQuestionItemLoader, ZhiHuQuestionItem


class ZhiHuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['zhihu.com']
    start_urls = ["http://zhihu.com"]

    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhizhu.com",
        'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0"
    }

    USER_NAME = 13439876152
    PASSWORD = 'chengchen0716'
    PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    COOKIES_PATH = os.path.join(PROJECT_DIR, 'temp', 'cookies.zhihu')

    answer_api_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B%2A%5D.is_normal" \
                     "%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail" \
                     "%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment" \
                     "%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission" \
                     "%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt" \
                     "%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp" \
                     "%2Cupvoted_followees%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author" \
                     ".follower_count%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}&sort_by" \
                     "=default "

    def start_requests(self):
        if os.path.exists(self.COOKIES_PATH):
            f = open(self.COOKIES_PATH, 'rb')
            cookies = pickle.load(f)
            f.close()
        else:
            browser = webdriver.Chrome(executable_path=os.path.join(
                self.PROJECT_DIR, 'chromedriver.exe'))

            browser.get('https://www.zhihu.com/signin')
            browser.find_element_by_css_selector(".SignFlow-accountInput.Input-wrapper input").send_keys(
                self.USER_NAME)
            browser.find_element_by_css_selector(".SignFlow-password input").send_keys(
                self.PASSWORD)
            browser.find_element_by_css_selector(
                ".Button.SignFlow-submitButton").click()
            time.sleep(5)
            cookies = browser.get_cookies()
            f = open(os.path.join(self.PROJECT_DIR, 'temp', 'cookies.zhihu'), 'wb')
            pickle.dump(cookies, f)
            f.close()
            browser.close()
        cookie_dict = {}
        for cookie in cookies:
            cookie_dict[cookie['name']] = cookie['value']

        return [scrapy.Request(url=self.start_urls[0], dont_filter=True, cookies=cookie_dict, headers=self.headers)]

    def parse(self, response):
        urls = response.css('a::attr("href")').extract()
        for url in urls:
            match_obj = re.match('^(/question/\d+).*', url)
            if match_obj:
                yield scrapy.Request(parse.urljoin(response.url, match_obj.group(1)), headers=self.headers, callback=self.parse_question)
            else:
                yield scrapy.Request(parse.urljoin(response.url, url), headers=self.headers, callback=self.parse)

    def parse_question(self, response):
        item_loader = ZhiHuQuestionItemLoader(item=ZhiHuQuestionItem(), response=response)
        item_loader.add_css('title', 'h1.QuestionHeader-title::text')
        item_loader.add_css('topics', '.QuestionTopic ::text')
        item_loader.add_css('comment_num', '.QuestionHeader-Comment button::text')
        item_loader.add_css('content', '.QuestionHeader-detail')
        item_loader.add_css('answers_num', '.List-headerText span::text')

        match_obj = re.match('.*?(\d+)$|/', response.url)
        item_loader.add_value('question_id', match_obj.group(1))

        article_item = item_loader.load_item()

        selector = response.css('strong.NumberBoard-itemValue::attr("title")').extract()
        article_item["watch_num"] = selector[0]
        article_item["click_num"] = selector[1]

        yield article_item
        pass

    def parse_answers(self, response):
        pass