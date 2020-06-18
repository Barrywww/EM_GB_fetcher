# -*- coding: utf-8 -*-

import time
import csv
import requests
import json
import random
import traceback
import re
import os
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

BASE_URL = 'http://guba.eastmoney.com'
USER_BASE_URL = "https://i.eastmoney.com"

# 字段定义：[吧名称，股票代码，作者，标题，类型，ID，点击量，评论数，发帖时间，URL]
GENERAL_HEADER = ['forum', 'stockid', 'author', 'title', 'category', 'identity', 'views', 'comments', 'time', 'link']
CATEGORY_MAP = {"资讯": "zixun", "研报": "yanbao", "问董秘": "askanswer", "公告": "gonggao", "热门": "hot", "": "discussion"}
INFLUENCE_MAP = {"stars0": "0", "stars05": "1", "stars1": "2", "stars15": "3", "stars2": "4",
                 "stars25": "5", "stars3": "6", "stars35": "7", "stars4": "8", "stars45": "9", "stars5": "10"}

# 字段定义：[帖子ID，评论ID，标题，内容，用户ID，发帖时间，点赞数，是否为一楼]
CONTENT_HEADER = ['threadID', 'replyID', 'title', 'content', 'UID', 'postTime', 'likes', 'isFirstPage']
TOTAL_PAGE_NUM = 10
PAGE_STEP = 100

TOTAL_COMMENTS = 0
OVERRIDE = False
THRESHOLD = 5
OVERRIDE_LIMIT = 5
boost = 5

whoops = int(time.time())
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options, executable_path="D:/Python/Selenium_Chrome_Driver/chromedriver.exe")
driver.set_page_load_timeout(3)
driver.set_script_timeout(3)

MODE0 = 0
MODE1 = 1


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
            # print("Correct, Writing")
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


def fetchForumLinks(forumID, THRESHOLD, mode, VERBOSE=False):
    COUNTER = 0
    forumID = str(forumID)
    # currentTimeStamp = int(time.time())
    # endTimeStamp = currentTimeStamp - (currentTimeStamp % 86400)
    # startTimeStamp = endTimeStamp - 86400
    pageNum = 1
    if os.path.exists("./"):
        pass
    if mode == MODE0:
        hi = whoops - 300
        # print(int(time.time()), hi)
    else:
        hi = (whoops - (whoops % 3600)) - 3600
    json_name = "./url_list/" + str(forumID) + ".json"
    if os.path.exists(json_name) and os.path.getsize(json_name) > 0:
        # print("Loading:", json_name)
        json_file = open(json_name, "r+", encoding="utf-8")
        thread_history = json.load(json_file)
    else:
        json_file = open(json_name, "a", encoding="utf-8")
        thread_history = {}
    INIT_YEAR = 2020
    prevMonth = 13
    flag = True
    writer = timeBasedWriter("./guba_general_data/guba_", toLocalTime(int(time.time())))
    while flag and COUNTER < THRESHOLD:
        url = BASE_URL + "/list," + forumID + "_" + str(pageNum) + ".html"
        print("Fetching URL:", url)
        COUNTER += 1
        web_source = requests.get(url)
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
                identity = details[2].select("a")[0].get("href")[1:-5]
                title = details[2].select("a")[0].get_text()
                if link[0] != "h":
                    link = BASE_URL + link
                else:
                    identity = link.split("/")[-1][:-5]
                if category == "askanswer":
                    link = details[2].select("a")[1].get("href")
                    link = BASE_URL + link
                    title = details[2].select("a")[1].get_text()
                    identity = link.split("/")[-1][:-5]

                general_result = {"forum": forumName[:-1],
                                  # "stockid": re_mode.search(articleInfo[0].get("href")).group()
                                  "stockid": forumID,
                                  "author": details[3].select("a > font")[0].get_text(),
                                  "title": title,
                                  "category": category,
                                  "identity": identity,
                                  "views": details[0].get_text().strip(),
                                  "comments": details[1].get_text().strip(),
                                  "time": date,
                                  "link": link
                                  }
                print(general_result)
                if toTimeStamp(date + ":" + "00") < hi:
                    flag = False
                    break
                prevMonth = int(date[5:7])
                # filename1 = "./guba_general_data/general_" + date[-5:-2] + ".csv"
                writer.writeRow(general_result.values(), date[:-3])
                thread_history[general_result["identity"].split(",")[-1]] = general_result["link"]
            # print(pageNum)
        else:
            json_file.write(json.dumps(thread_history))
            break
        pageNum += 1
        time.sleep(random.randint(1, boost))
    writer.close()
    json_file.write(json.dumps(thread_history))
    json_file.close()


def FetchBodyContent(inst, testFlag = False):
    url = inst[:-5] + ".html"
    print("Now Fetching:", url)
    try:
        driver.get(url)
    except TimeoutException:
        return
    # print(body.text)
    soup = BeautifulSoup(driver.page_source.encode("utf-8"), "lxml")
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
            time.sleep(random.randint(1, boost))
            # contentWriter.writeRow(list(page_content.values()), page_content["postTime"][:-6])
            with open("./guba_content_data/guba_content_" + page_content["postTime"][:-6] + ".csv", "a",
                      encoding="utf-8", newline="") as csvfile:
                writer = csv.writer(csvfile, delimiter="ǁ")
                writer.writerow(list(page_content.values()))

            numcomments = int(soup.select("#stockheader > div > div > span.tc1.replyCount")[0].get_text())
            if numcomments > 0:
                # print("Total comments:", numcomments)
                FetchReplies(inst, page_content["threadID"], page_content["postTime"])
            else:
                print("No comments, skipping.")
        else:
            print(page_content)
            time.sleep(random.randint(1, boost))
        global TOTAL_COMMENTS
        TOTAL_COMMENTS += 1
    else:
        if testFlag:
            print("URL:" + url + " DOES NOT EXIST, SKIPPING............")
    # contentWriter.close()


def FetchReplies(inst, threadID, postTime, testFlag=False):
    global TOTAL_COMMENTS
    page_counter = 1
    while True:
        url = inst[:-5] + "_" + str(page_counter) + ".html"
        # print(url)
        if page_counter != 1:
            try:
                driver.get(url)
                WebDriverWait(driver, timeout=2).until(
                    EC.visibility_of_any_elements_located((By.CSS_SELECTOR, "#comment_all_content > div > div")))
            except TimeoutException:
                print("NORMAL COMMENTS: Timeout, skipping")
        replies = driver.find_elements_by_css_selector("#comment_all_content > div > div")
        num_comments = len(replies)
        print("Num of NORMAL Comments:", num_comments)
        if num_comments == 0:
            break
        else:
            for r in range(num_comments):
                reply_result = {"threadID": threadID,
                                "replyID": replies[r].get_attribute("data-reply_id"),
                                "title": "",
                                "content": replies[r].find_element_by_css_selector("div > div.level1_reply_cont > \
                                div.short_text").text.strip(),
                                "UID": replies[r].find_element_by_css_selector("div > div.replyer_info > a")
                                .get_attribute("data-popper"),
                                "postTime":replies[r].find_element_by_css_selector("div > div.publish_time").text[4:23],
                                "likes": replies[r].get_attribute("data-reply_like_count") or "0",
                                "isFirst": False,
                               }
                # print(postTime, reply_result["postTime"])
                print("Replied within 5 DAYS:", toTimeStamp(reply_result["postTime"]) - toTimeStamp(postTime) <= 432000)
                print(reply_result)
                if not testFlag and (toTimeStamp(reply_result["postTime"]) - toTimeStamp(postTime) <= 432000):
                    with open("./guba_content_data/guba_content_" + reply_result["postTime"][:-6] + ".csv", "a",
                              encoding="utf-8", newline="") as csvfile:
                        writer = csv.writer(csvfile, delimiter="ǁ")
                        writer.writerow(list(reply_result.values()))
                        un = "./user_list/" + reply_result["postTime"][:-6] + ".json"
                        if os.path.exists(un) and os.path.getsize(un) > 0:
                            print("Loading:", un)
                            ujf = open(un, "r+", encoding="utf-8")
                            uh = json.load(ujf)
                        else:
                            ujf = open(un, "w", encoding="utf-8")
                            uh = {}
                        if uh.get(reply_result["UID"], -1) != -1:
                            uh[reply_result["UID"]] += 1
                        else:
                            uh[reply_result["UID"]] = 1
                        ujf.seek(0)
                        print(uh)
                        ujf.write(json.dumps(uh))
                        ujf.close()
                    TOTAL_COMMENTS += 1
                else:
                    pass
        page_counter += 1
        if num_comments < 30:
            break
        time.sleep(random.randrange(1, boost))


def fetchUserById(uid, ttt):
    url = USER_BASE_URL + "/" + str(uid)
    web_source = requests.get(url)
    soup = BeautifulSoup(web_source.content.decode("utf-8"), "lxml")
    views = soup.select("#others > div > div.others_top > div.others_content > div.others_info > p")[0].select("span")
    user_data = {
        "username": soup.select("#others > div > div.others_top > div.others_content > div.others_title > div.others_username")[0].get_text().strip(),
        "influence": INFLUENCE_MAP[soup.select("#influ_star")[0].get("class")[0]],
        "age": soup.select("#others > div > div.others_top > div.others_content > div.others_title > div.others_level > p")[1].select("span")[0].get_text()[:-1],
        "following": soup.select("#tafollownav > p > span")[0].get_text(),
        "fans": soup.select("#tafansa > p > span")[0].get_text(),
        "total_view": views[0].get_text(),
        "today_view": views[1].get_text()
    }
    with open("./user_data/user_" + ttt + ".csv", "a", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter="ǁ")
        writer.writerow(list(user_data.values()))


def ufsr(fn):
    fn1 = "./user_list/" + fn
    with open(fn1, "r") as f:
        fjs = json.load(f)
        for k in fjs.keys():
            fetchUserById(k, fn[5:-4])


def generalFetcher(forumList, mode, VERBOSE=False):
    for id in forumList:
        fetchForumLinks(id, THRESHOLD, mode, VERBOSE)


def bodyFetcher(forumList):
    for forumID in forumList:
        json_name = "./url_list/" + str(forumID) + ".json"
        json_file = open("./url_list/" + str(forumID) + ".json", "r", encoding="utf-8")
        if os.path.getsize(json_name) > 0:
            json_dic = json.load(json_file)
            # print(json_dic)
            for urls in json_dic.values():
                FetchBodyContent(urls)
        json_file.close()


if __name__ == "__main__":
    try:
        sf = open("stockid.csv", "r", encoding="utf-8")
        lissy = csv.reader(sf)
        sli = list(lissy)[0][:100]
        generalFetcher(forumList=sli, mode=MODE0, VERBOSE=False)
        bodyFetcher(forumList=sli)
        for ul in os.listdir("./user_list"):
            ufsr(ul)
            
    except Exception as err:
        print(err)
        print(traceback.print_exc())
        driver.quit()
