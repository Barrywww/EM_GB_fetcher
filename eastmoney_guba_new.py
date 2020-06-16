# -*- coding: utf-8 -*-

import time
import csv
import requests
import json
import re
import os
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

BASE_URL = 'http://guba.eastmoney.com'

# 字段定义：[吧名称，股票代码，作者，标题，类型，ID，点击量，评论数，发帖时间，URL]
GENERAL_HEADER = ['forum', 'stockid', 'author', 'title', 'category', 'identity', 'views', 'comments', 'time', 'link']
CATEGORY_MAP = {"资讯": "zixun", "研报": "yanbao", "问董秘": "askanswer", "公告": "gonggao", "热门": "hot", "": "discussion"}

# 字段定义：[帖子ID，评论ID，标题，内容，用户ID，发帖时间，点赞数，是否为一楼]
CONTENT_HEADER = ['threadID', 'replyID', 'title', 'content', 'UID', 'postTime', 'likes', 'isFirstPage']
STOCK_FILE_GUBA = "./stock_data_"
STOCK_URL_GUBA = "./stock_url_"
TOTAL_PAGE_NUM = 10
PAGE_STEP = 100

TOTAL_COMMENTS = 0
OVERRIDE = False
COUNTER = 0
THRESHOLD = 3
OVERRIDE_LIMIT = 5

UA = UserAgent()


STOCK_THREAD_FILE = "./thread_data_"
BASE_URLSOURCE = "stock_url_00000.txt"

# soup.select("#zwconbody > div")[0].get_text().replace(u"\u3000", "\n")
# soup.select("#zwlist")[0].get_text().strip()
# soup.select("#zwlist > div.zwli.clearfix")[1].get("data-reply_like_count")


class timeBasedWriter():
    def __init__(self, basename, localTime):
        self._basename = basename
        self._suffix = ".csv"
        self._time = localTime
        self._fileName = self._basename + self._time + self._suffix
        self._file = open(self._fileName, "a+", encoding="utf-8", newline="")
        self._writer = csv.writer(self._file, delimiter="ǁ")
    
    def close(self):
        self._file.close()

    def flush(self):
        self._file.flush()
    
    def reload(self, localTime):
        self._file.close()
        self._time = localTime
        self._fileName = self._basename + self._time + self._suffix
        self._file = open(self._fileName, "a+", encoding="utf-8", newline="")
        self._writer = csv.writer(self._file, delimiter="ǁ")
    
    def getSize(self):
        return os.path.getsize(self._fileName)

    def getTime(self):
        return self._time
    
    def writeRow(self, row, localTime):
        if self.checkTime(localTime):
            print("Correct, Writing")
            if self.getSize() == 0:
                self._writer.writerow(GENERAL_HEADER)
                self._file.flush()
            self._writer.writerow(row)
        else:
            self.reload(localTime)
            self.writeRow(row, localTime)

    def checkTime(self, localTime):
        if self._time == localTime:
            return True
        else:
            return False


def toTimeStamp(dttime):
    return int(time.mktime(time.strptime(dttime, "%Y-%m-%d %H:%M:%S")))


def toLocalTime(tgtTimeStamp):
    return time.strftime("%Y-%m-%d %H", time.localtime(tgtTimeStamp))


def fetchForumLinks(forumID, VERBOSE=False):
    global COUNTER, THRESHOLD
    COUNTER, THRESHOLD = 0, 0
    forumID = str(forumID)
    # currentTimeStamp = int(time.time())
    # endTimeStamp = currentTimeStamp - (currentTimeStamp % 86400)
    # startTimeStamp = endTimeStamp - 86400
    pageNum = 1
    json_name = "./url_list/" + str(forumID) + ".json"
    if os.path.exists(json_name) and os.path.getsize(json_name) > 0:
        print("Loading:", json_name)
        json_file = open(json_name, "r+", encoding="utf-8")
        thread_history = json.load(json_file)
    else:
        json_file = open(json_name, "a", encoding="utf-8")
        thread_history = {}
    INIT_YEAR = 2020
    prevMonth = 13
    writer = timeBasedWriter("./guba_general_data/guba_", toLocalTime(int(time.time())))
    while True and (VERBOSE and COUNTER <= THRESHOLD):
        url = BASE_URL + "/list," + forumID + "_" + str(pageNum) + ".html"
        print("Fetching URL:", url)
        COUNTER += 1
        web_source = requests.get(url, headers={"User-Agent": UA.random})
        soup = BeautifulSoup(web_source.content.decode("utf-8"), "lxml")
        threadList = soup.select("#articlelistnew > div.normal_post")
        forumName = soup.select("#stockname > a")[0].get_text()
        if len(threadList) != 0:
            for t in threadList:
                details = t.select("span")
                date = details[4].get_text()
                if int(date[3:5]) > prevMonth and prevMonth == 1:
                    INIT_YEAR -= 1
                date = str(INIT_YEAR) + "-" + date
                category = details[2].select("em")
                if len(category) == 0:
                    category = "discussion"
                else:
                    category = CATEGORY_MAP[category[0].get_text()]

                link = details[2].select("a")[0].get("href")
                if link[0] != "h":
                    link = BASE_URL + link

                general_result = {"forum": forumName[:-1],
                                  # "stockid": re_mode.search(articleInfo[0].get("href")).group()
                                  "stockid": forumID,
                                  "author": details[3].select("a > font")[0].get_text(),
                                  "title": details[2].select("a")[0].get_text(),
                                  "category": category,
                                  "identity": details[2].select("a")[0].get("href")[1:-5],
                                  "views": details[0].get_text().strip(),
                                  "comments": details[1].get_text().strip(),
                                  "time": date,
                                  "link": link
                                  }
                print(general_result)
                # filename1 = "./guba_general_data/general_" + date[-5:-2] + ".csv"
                writer.writeRow(general_result.values(), date[:-3])
                thread_history[general_result["identity"].split(",")[-1]] = general_result["link"]
            print(pageNum)
        else:
            json_file.write(json.dumps(thread_history))
            break
        pageNum += 1
        time.sleep(1)
    writer.close()
    json_file.write(json.dumps(thread_history))


def FetchBodyContent(inst, testFlag = False):
    url = inst[:-5] + "_1" + ".html"
    print(url)
    body = requests.get(url, headers={"User-Agent": UA.random})
    # print(body.text)
    soup = BeautifulSoup(body.content.decode("utf-8"), "lxml")
    # contentWriter = timeBasedWriter("./guba_body_data/guba_", toLocalTime(int(time.time())))
    if testFlag:
        print("Fetching URL:", url)
    if soup.select("title")[0].get_text() != "":
        # thread_title = soup.select("#zwconttbt")[0].get_text().strip()
        qa = soup.select("#zwcontent > div.zwcontentmain > div.qa")
        if len(soup.select("#zw_body")) != 0:
            thread_content = soup.select("#zw_body")[0].get_text().strip()
            title = soup.select("#zwconttbt")[0].get_text().strip()
        elif qa:
            title = "问：" + qa[0].select("div.question > div")[0].get_text().strip()
            thread_content = "答：" + qa[0].select("div.answer_wrap > div > div.content_wrap > div.content")[0].get_text().strip().replace(u"\u3000", " ")
        else:
            thread_content = soup.select("#zwconbody > div")[0].get_text().strip()
            title = soup.select("#zwconttbt")[0].get_text().strip()
        page_content = {"threadID": url.split("/")[-1][:-5],
                      "replyID": "0",
                      "title": title,
                      "content": thread_content,
                      "UID": soup.select("#zwconttbn > strong > a")[0].get("data-popper"),
                      "postTime": soup.select("#zwconttb > div.zwfbtime")[0].get_text()[4:23],
                      "likes": soup.select("#like_wrap")[0].get("data-like_count") or "0",
                      "isFirst": True,
                      }
        print(page_content)
        if not testFlag:
            # contentWriter.writeRow(list(page_content.values()), page_content["postTime"][:-6])
            with open("./guba_content_data/guba_content_" + page_content["postTime"][:-6] + ".csv", "a", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(list(page_content.values()))


            FetchReplies(inst, soup, page_content["threadID"], page_content["postTime"])
        else:
            print(page_content)
            time.sleep(0.5)
        global TOTAL_COMMENTS
        TOTAL_COMMENTS += 1
    else:
        if testFlag:
            print("URL:" + url + " DOES NOT EXIST, SKIPPING............")
    # contentWriter.close()
    time.sleep(1)


def FetchReplies(inst, soup, threadID, postTime, testFlag=False):
    global TOTAL_COMMENTS
    hot_replies = soup.select("#comment_hot_content > div > div")
    # replyWriter = timeBasedWriter("./guba_body_data/guba_content_", postTime)
    print("Fetching Replies", len(hot_replies))
    for r in range(len(hot_replies)):
        hot_result = {"threadID": threadID,
                      "replyID": hot_replies[r].get("data-reply_id"),
                      "title": "",
                      "content": hot_replies[r].select("div > div.level1_reply_cont > div.full_text")[0].get_text().strip(),
                      "UID": hot_replies[r].select("div > div.replyer_info > a").get("data-popper"),
                      "postTime": hot_replies[r].select("div > div.publish_time")[0].get_text()[4:23],
                      "likes": hot_replies[r].get("data-reply_like_count") or "0",
                      "isFirst": False,
        }
        print(hot_result)
        if not testFlag:
            with open("./guba_content_data/guba_content_" + hot_result["postTime"][:-6] + ".csv", "a", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile, delimiter="ǁ")
                writer.writerow(list(hot_result.values()))
            # contentWriter.writeRow(list(hot_result.values()))
            TOTAL_COMMENTS += 1
        else:
            print(hot_result)
    page_counter = 1
    while True:
        url = inst[:-5] + "_" + str(page_counter) + ".html"
        # print(url)
        web_content = requests.get(url, headers={"User-Agent": UA.random})
        soup = BeautifulSoup(web_content.content.decode("utf-8"), "lxml")
        replies = soup.select("#comment_hot_content > div > div")
        num_comments = len(replies)
        print("num_comments", num_comments)
        if num_comments == 0:
            break
        else:
            for r in range(num_comments):
                # print("-------"+str(r)+"-------")
                contents = replies[r].select("div.zwlitx > div > div.zwlitext.stockcodec > div")
                reply_result = {"threadID": threadID,
                              "replyID": hot_replies[r].get("data-reply_id"),
                              "title": "",
                              "content": hot_replies[r].select("div > div.level1_reply_cont > div.full_text")[0].get_text().strip(),
                              "UID": hot_replies[r].select("div > div.replyer_info > a").get("data-popper"),
                              "postTime": hot_replies[r].select("div > div.publish_time")[0].get_text()[4:23],
                              "likes": replies[r].get("data-reply_like_count") or "0",
                              "isFirst": False,
                              }
                print(postTime, reply_result["postTime"])
                print(toTimeStamp(reply_result[postTime]) - toTimeStamp(postTime) <= 432000)
                print(reply_result)
                if not testFlag and (toTimeStamp(reply_result[postTime]) - toTimeStamp(postTime) <= 432000):
                    with open("./guba_content_data/guba_content_" + reply_result["postTime"][:-6] + ".csv", "a",
                              encoding="utf-8") as csvfile:
                        writer = csv.writer(csvfile, delimiter="ǁ")
                        writer.writerow(list(reply_result.values()))
                    TOTAL_COMMENTS += 1
                else:
                    print(reply_result)
        page_counter += 1
        time.sleep(1)


def generalFetcher(forumList, VERBOSE=False):
    for id in forumList:
        fetchForumLinks(id, VERBOSE)


def bodyFetcher(forumList):
    for forumID in forumList:
        json_name = "./url_list/" + str(forumID) + ".json"
        json_file = open("./url_list/" + str(forumID) + ".json", "r", encoding="utf-8")
        if os.path.getsize(json_name) > 0:
            json_dic = json.load(json_file)
            # print(json_dic)
            for urls in json_dic.values():
                FetchBodyContent(urls)


if __name__ == "__main__":
    generalFetcher(forumList=[603986], VERBOSE=True)
    bodyFetcher(forumList=[603986])
