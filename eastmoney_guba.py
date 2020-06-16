# -*- coding: utf-8 -*-
import time, datetime
import csv
import requests
import json
import re
import os
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

REQUEST_HEADER = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36'}
BASE_URL = 'http://guba.eastmoney.com'

STOCK_GROUP_FILE = 'D:/trading/model/stock_group.csv'
STOCK_HOLDER_TOP10_FILE = 'D:/trading/model/stock_floatingholder.csv'

# 字段定义：[吧名称，股票代码，作者，标题，类型，ID，点击量，评论数，发帖时间，URL]
GENERAL_HEADER = ['forum', 'stockid', 'author', 'title', 'category', 'identity', 'views', 'comments', 'time', 'link']
CATEGORY_MAP = {"icon_list_zixun": "zixun", "icon_list_yanbao": "yanbao", "icon_list_askanswer": "askanswer","icon_list_gonggao": "gonggao", "icon_list_hot": "hot"}

# 字段定义：[帖子ID，评论ID，标题，内容，用户ID，发帖时间，点赞数，是否为一楼]
CONTENT_HEADER = ['threadID', 'replyID', 'title', 'content', 'UID', 'postTime', 'likes', 'isFirstPage']
STOCK_FILE_GUBA = "./stock_data_"
STOCK_URL_GUBA = "./stock_url_"
TOTAL_PAGE_NUM = 10
PAGE_STEP = 100

TOTAL_COMMENTS = 0
OVERRIDE = False
COUNTER = 1
OVERRIDE_LIMIT = 5

UA = UserAgent()


STOCK_THREAD_FILE = "./thread_data_"
BASE_URLSOURCE = "stock_url_00000.txt"

# soup.select("#zwconbody > div")[0].get_text().replace(u"\u3000", "\n")
# soup.select("#zwlist")[0].get_text().strip()
# soup.select("#zwlist > div.zwli.clearfix")[1].get("data-reply_like_count")


class FileWriter:
    def __init__(self, basename, step=5000, mode="NUMBASE"):
        self._basename = basename
        self._suffix = ".csv"
        self._filecount = 0
        self._currentline = 0
        self._step = step
        self._mode = mode
        self._file = open("./" + self._basename + "%05d" % self._filecount
                          + self._suffix, "a", encoding="utf-8", newline="")
        self._writer = csv.writer(self._file, delimiter="ǁ")

    def writeRow(self, row):
        if self._mode == "NUMBASE":
            if self._currentline <= self._step:
                self._writer.writerow(row)
                self._currentline += 1
            else:
                self._file.close()
                self._filecount += 1
                self._currentline = 0
                self.loadFile()
                self._writer.writerow(row)
                self._currentline += 1
        elif self._mode == "TIMEBASE":
            self._writer.writerow(row)
        time.sleep(0.5)

    def loadFile(self):
        print("opening new file:" + "./" + self._basename + "%05d" % self._filecount
                          + self._suffix)
        self._file = open("./" + self._basename + "%05d" % self._filecount
                          + self._suffix, "a", encoding="utf-8", newline="")
        self._writer = csv.writer(self._file, delimiter="ǁ")
        print("file_loaded")

    def close(self):
        self._file.close()


def FetchBodyContent(inst, testFlag = False):
    url = inst[:-5] + "_1" + ".html"
    # print(url)
    body = requests.get(url, headers=REQUEST_HEADER)
    # print(body.text)
    soup = BeautifulSoup(body.content.decode("utf-8"), "lxml")
    if testFlag:
        print("Fetching URL:", url)
    if soup.select("title")[0].get_text() != "":
        # thread_title = soup.select("#zwconttbt")[0].get_text().strip()
        qa = soup.select("#zwcontent > div.zwcontentmain > div.qa")
        if len(soup.select("#zw_body")) != 0:
            thread_content = soup.select("#zw_body")[0].get_text().strip()
            title = soup.select("#zwconttbt")[0].get_text().strip()
        elif qa:
            title = "问：" + qa[0].select("div.question > div")[0].get_text().strip().replace(u"\u3000", " ")
            thread_content = "答：" + qa[0].select("div.answer_wrap > div > div.content_wrap > div.content")[0].get_text().strip().replace(u"\u3000", " ")
        else:
            thread_content = soup.select("#zwconbody > div")[0].get_text().strip().replace(u"\u3000", " ")
            title = soup.select("#zwconttbt")[0].get_text().strip()
        page_content = {"threadID": url.split("/")[-1][:-5],
                      "replyID": "0",
                      "title": title,
                      "content": thread_content,
                      "UID": soup.select("#zwconttbn > strong > a")[0].get("data-popper"),
                      "postTime": soup.select("#zwconttb > div.zwfbtime")[0].get_text()[4:24],
                      "likes": soup.select("#like_wrap")[0].get("data-like_count") or "0",
                      "isFirstPage": True,
                      }
        if not testFlag:
            contentWriter.writeRow(list(page_content.values()))

            FetchReplies(inst, soup, page_content["threadID"])
        else:
            print(page_content)
            time.sleep(0.5)
        global TOTAL_COMMENTS
        TOTAL_COMMENTS += 1
    else:
        if testFlag:
            print("URL:" + url + " DOES NOT EXIST, SKIPPING............")


def FetchReplies(inst, soup, threadID, testFlag=False):
    global TOTAL_COMMENTS
    hot_replies = soup.select("#zwlist_hot > div.zwli.clearfix")
    for r in range(len(hot_replies)):
        hot_result = {"threadID": threadID,
                      "replyID": hot_replies[r].get("data-huifuid"),
                      "title": "",
                      "content": hot_replies[r].select("div.zwlitx > div > div.zwlitext.stockcodec > div")[0].get_text().strip().replace(u"\u3000", " "),
                      "UID": hot_replies[r].select("div.zwliimg > a")[0].get("href").split("/")[-1],
                      "postTime": hot_replies[r].select("div.zwlitx > div > div.zwlitime")[0].get_text()[4:24],
                      "likes": hot_replies[r].get("data-reply_like_count") or "0",
                      "isFirstPage": False,
        }
        if not testFlag:
            contentWriter.writeRow(list(hot_result.values()))
            TOTAL_COMMENTS += 1
        else:
            print(hot_result)
    page_counter = 1
    while True:
        url = inst[:-5] + "_" + str(page_counter) + ".html"
        # print(url)
        web_content = requests.get(url, headers=REQUEST_HEADER)
        soup = BeautifulSoup(web_content.content.decode("utf-8"), "lxml")
        replies = soup.select("#zwlist > div.zwli.clearfix")
        num_comments = len(replies)
        # print("num_comments", num_comments)
        if num_comments == 0:
            break
        else:
            for r in range(num_comments):
                # print("-------"+str(r)+"-------")
                contents = replies[r].select("div.zwlitx > div > div.zwlitext.stockcodec > div")
                reply_result = {"threadID": threadID,
                              "replyID": replies[r].get("data-huifuid"),
                              "title": "",
                              "content": contents[0].get_text().strip().replace(u"\u3000", " "),
                              "UID": replies[r].select("div.zwliimg > a")[0].get("href").split("/")[-1],
                              "postTime": replies[r].select("div.zwlitx > div > div.zwlitime")[0].get_text()[4:24],
                              "likes": replies[r].get("data-reply_like_count") or "0",
                              "isFirstPage": False,
                              }
                if not testFlag:
                    contentWriter.writeRow(list(reply_result.values()))
                    TOTAL_COMMENTS += 1
                else:
                    print(reply_result)
        page_counter += 1

# 用来抓取某URL前后几页的数据，已弃用
'''def findAround(url, mode, tgtTimeStamp):
    subURL = url[:-5].split("_")
    urlList = []
    threadList = []
    if mode == "forward":
        for offset in range(3, 0, -1):
            urlList.append(subURL[0] + str(int(subURL[-1]) - offset) + ".html")
    elif mode == "backward":
        for offset in range(1, 4):
            urlList.append(subURL[0] + str(int(subURL[-1]) + offset) + ".html")

    for urls in urlList:
        web_source = requests.get(urls, headers={"User-Agent": UA.random})
        soup = BeautifulSoup(web_source.content.decode("utf-8"), "lxml")
        sections = soup.select("#main-body > div.guba_cont.clearfix > div.list_cont > div.wrap > div > div.cont.bg.gbbb1 > div.balist > ul > li")
        for threads in sections:
            threadList.append({"id": threads.select("span > a")[1].get("href")[:-5],
                               "time": toTimeStamp(threads.select(".last")[0].get_text())})'''

def findThreadID(sections, tgtTimeStamp, mode="first"):
    threadsList = []
    for threads in sections:
        threadTime = toTimeStamp("2020-" + threads.select(".last")[0].get_text())
        if threadTime == tgtTimeStamp:
            if mode == "last":
                return threads.select("span > a")[1].get("href")[1:-5]
            elif mode == "first":
                threadsList.append(threads.select("span > a")[1].get("href")[1:-5])
    return threadsList[-1]


def findTimeInPage(url, tgtTimeStamp):
    print("Finding in URL:", url)
    web_content = requests.get(url, headers={"User-Agent": UA.random})
    time.sleep(0.5)
    soup = BeautifulSoup(web_content.content.decode("utf-8"), "lxml")
    sections = soup.select("#main-body > div.guba_cont.clearfix > div.list_cont > div.wrap > div > div.cont.bg.gbbb1 > div.balist > ul > li")
    firstTime = toTimeStamp("2020-" + sections[-1].select(".last")[0].get_text())
    lastTime = toTimeStamp("2020-" + sections[0].select(".last")[0].get_text())
    # print("Page First Post Time:", sections[-1].select(".last")[0].get_text())
    # print("Page Last Post Time:", sections[0].select(".last")[0].get_text())
    # print(firstTime, lastTime)
    if firstTime <= tgtTimeStamp <= lastTime:
        print("Found AT URL:", url)
        return ["this", sections]
    elif tgtTimeStamp < lastTime:
        return ["right", lastTime]
    else:
        return ["left", firstTime]


# dttime格式： YYYY-MM-DD HH:MM
def findThread(tgtTimeStamp, mode):
    # tgtTimeStamp = toTimeStamp(dttime)
    page_num = 1
    interval = pageInterval(tgtTimeStamp)
    page_num += interval
    page_history = []
    while True:
        url = BASE_URL + "/default,0_" + str(page_num) + ".html"
        pageTimeResult = findTimeInPage(url, tgtTimeStamp)
        if page_history.count(page_num) >= 5:
            page_num = 1
            interval = pageInterval(tgtTimeStamp)
            page_num += interval
            page_history = []
        elif pageTimeResult[0] == "left":
            interval = max(interval // 2, 1)
            page_num -= interval
            page_history.append(page_num)
            # page_num -= pageInterval(pageTimeResult[1], tgtTimeStamp)
        elif pageTimeResult[0] == "right":
            interval = max(interval // 2, 1)
            page_num += interval
            page_history.append(page_num)
            # page_num += pageInterval(tgtTimeStamp, pageTimeResult[1])
        elif pageTimeResult[0] == "this":
            return findThreadID(pageTimeResult[1], tgtTimeStamp, mode)
        else:
            print("Error in fetching data on:", toLocalTime(tgtTimeStamp))
            raise(ValueError("Fetching Error."))


def toTimeStamp(dttime):
    return int(time.mktime(time.strptime(dttime, "%Y-%m-%d %H:%M")))

def toLocalTime(tgtTimeStamp):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(tgtTimeStamp))


def pageInterval(tgttime, curtime=int(time.time())):

    timeDiff = curtime - tgttime
    if timeDiff < 0:
        assert "Time Error"
    elif timeDiff >= 86400:
        return 3000 * (timeDiff // 86400)
    elif timeDiff >= 33200:
        return 1500
    elif timeDiff >= 14400:
        return 500
    elif timeDiff >= 3600:
        return 125
    elif timeDiff >= 1800:
        return 60
    else:
        return 10


def FetchUserInfo(url):
    pass


def FetchWebTable(inst):
    global COUNTER
    url = BASE_URL + "/default,0_" + inst + ".html"
    web_source = requests.get(url, headers=REQUEST_HEADER)
    soup = BeautifulSoup(web_source.content.decode("utf-8"), 'lxml')
    # print(soup)

    sections = soup.select("#main-body > div.guba_cont.clearfix > div.list_cont > div.wrap > div > div.cont.bg.gbbb1 > div.balist > ul > li")
    # print(sections)
    # print(len(sections))

    # re_mode = re.compile(r"\d+")
    for items in sections:
        if OVERRIDE and OVERRIDE_LIMIT > COUNTER:
            COUNTER += 1
        elif OVERRIDE:
            return
        # 包括文章的链接、标题
        articleInfo = items.select("span > a")
        # 文章的阅读量、评论量
        stats = items.select("cite")
        tags = items.select("span > em")
        category = []
        if len(tags) > 0:
            for t in tags:
                # print(t.get("class"))
                tag = CATEGORY_MAP.get(t.get("class")[-1])
                if tag:
                    category.append(tag)
        if len(category) == 0:
            category.append("discussion")


        print(general_result)

        generalWriter.writeRow(general_result.values())

        FetchBodyContent(general_result["link"])
        
        # time.sleep(0.3)

        # yield general_result

# timespan参数：tuple对象，("开始时间"，“结束时间”)
# 例： ("2020-06-07", "2020-06-09")
# 2020-06-10 弃用此函数
def timeBaseFetcher(timespan):
    global COUNTER
    local_base_url = "http://guba.eastmoney.com/news,300829,"
    startTimeStamp = toTimeStamp(timespan[0] + " 00:00")
    endTimeStamp = min(toTimeStamp(timespan[1] + " 23:59"), int(time.time()))
    nextTimeStamp = startTimeStamp + 86400
    print(startTimeStamp, endTimeStamp, nextTimeStamp, int(time.time()))
    while nextTimeStamp <= endTimeStamp + 60:
        startThread = findThread(startTimeStamp, "first")
        endThread = findThread(endTimeStamp, "last")
        startThreadID = int(startThread.split(",")[-1])
        endThreadID = int(endThread.split(",")[-1])
        for threadidx in range(startThreadID, endThreadID + 1):
            url = local_base_url + str(threadidx) + ".html"
            print("Fetching:", url)
            web_source = requests.get(url, headers=REQUEST_HEADER)
            soup = BeautifulSoup(web_source.content.decode("utf-8"), 'lxml')
            title = soup.select("#zwconttbt")[0].get_text().split()
            if len(title) == 0:
                title = soup.select("title")[0].get_text().split("_")[0]

            # if len(soup.select("body > div.gbbody.jjbody")) > 0:
            #     stats = soup.select("#zwmbtilr > div > span")
            # else:
            #     stats = soup.select("#stockheader > div > div > span")

            if soup.select("title")[0].get_text() != "":
                general_result = {"forum": soup.select("#stockname > a")[0].get_text()[:-1],
                                  # "stockid": re_mode.search(articleInfo[0].get("href")).group()
                                  "stockid": soup.select("#stockname")[0].get("data-popstock"),
                                  "author": soup.select("#zwconttbn > strong > a > font")[0].get_text(),
                                  "title": title,
                                  # "category": "&".join(category),
                                  "identity": soup.select("head > link")[0].get("href")[1:-5],
                                  # "views": stats[0].get_text(),
                                  # "comments": stats[1].get_text(),
                                  "time": soup.select("#zwconttb > div.zwfbtime")[0].get_text()[4:24],
                                  "link": BASE_URL + soup.select("head > link")[0].get("href")[1:-5]
                                  }

                print(general_result)

        nextTimeStamp += 86400

if __name__ == '__main__':
    '''for i in range(1, TOTAL_PAGE_NUM+1, PAGE_STEP):
        print("--------Crawling Page " + str(i) + " to " + str(min(TOTAL_PAGE_NUM, (i+PAGE_STEP-1))) + "--------")
        # 按步进保存到CSV文件
        with open(STOCK_FILE_GUBA + "%05d" % (i//PAGE_STEP) + ".csv", "a", newline='') as csvfile:
            # 独立存储URL的文件
            with open(STOCK_URL_GUBA + "%05d" % (i // PAGE_STEP) + ".txt", "a", newline='') as urlfile:
                writer = csv.writer(csvfile, delimiter='|')
                writer.writerow(HEADER)
                for k in range(i, min(i+PAGE_STEP, TOTAL_PAGE_NUM)):
                    for stocks in FetchWebTable(str(i)):
                        # 写入字典的内容
                        writer.writerow(list(stocks.values()))
                        # 写入URL
                        urlfile.write(stocks["link"]+"\n")
        time.sleep(0.5)'''

    os.mkdir("./guba_general_data")
    os.mkdir("./guba_body_data")
    # os.mkdir("./guba_user_data")
    generalWriter = FileWriter("./guba_general_data/guba_general_data_", mode="TIMEBASE")
    contentWriter = FileWriter("./guba_body_data/guba_body_data_", mode="TIMEBASE")
    # userWriter = FileWriter("./guba_user_data/guba_user_data_", mode="TIMEBASE")

    generalWriter.writeRow(GENERAL_HEADER)
    contentWriter.writeRow(CONTENT_HEADER)

    timeBaseFetcher(("2020-06-09", "2020-06-09"))

    # for i in range(1, TOTAL_PAGE_NUM+1):
    #     FetchWebTable(str(i))


    # print(TOTAL_COMMENTS)
    generalWriter.close()
    contentWriter.close()
    # userWriter.close()

  

