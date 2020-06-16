# -*- coding: utf-8 -*-
import time
import csv
import requests
import re
from bs4 import BeautifulSoup

REQUEST_HEADER = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
BASE_URL = 'http://guba.eastmoney.com'

STOCK_THREAD_FILE = "./thread_data_"
BASE_URLSOURCE = "stock_url_00000.txt"

# soup.select("#zwconbody > div")[0].get_text().replace(u"\u3000", "\n")
# soup.select("#zwlist")[0].get_text().strip()
# soup.select("#zwlist > div.zwli.clearfix")[1].get("data-reply_like_count")


class FileWriter:
    def __init__(self, basename, step=5000):
        self._basename = basename
        self._suffix = ".csv"
        self._filecount = 0
        self._currentline = 0
        self._step = step
        self._file = open("./" + self._basename + "%05d" % self._filecount
                          + self._suffix, "a", encoding="utf-8", newline="")
        self._writer = csv.writer(self._file, dilimiter="@@@")

    def writerow(self, row):
        if self._filecount <= self._step:
            self._writer.writerow(row)
            self._currentline += 1
        else:
            self._file.close()
            self._filecount += 1
            self._currentline = 0

    def loadFile(self):
        self._file = open("./" + self._basename + "%05d" % self._filecount
                          + self._suffix, "a", encoding="utf-8", newline="")


def FetchBodyContent(inst):
    url = inst[:-5] + "_1" + ".html"
    body = requests.get(url, header=REQUEST_HEADER)
    soup = BeautifulSoup(body.content.decode("utf-8"), "lxml")
    if body.status_code == 200:
        # thread_title = soup.select("#zwconttbt")[0].get_text().strip()
        if len(soup.select("#zw_body")) != 0:
            thread_content = soup.select("#zw_body")[0].get_text().strip()
        else:
            thread_content = soup.select("#zwconbody > div")[0].get_text().strip()
        result = {"threadID": inst.split("/")[-1][:-5],
                  "title": soup.select("#zwconttbt")[0].get_text().strip(),
                  "content": thread_content,
                  "UID": soup.select("#zwconttbn > strong > a")[0].get("data-popper"),
                  "postTime": soup.select("#zwconttb > div.zwfbtime")[0].get_text()[5:24],
                  }

        while FetchReplies(url):
            pass


def FetchReplies(url):
    return False

def fetchThread(inst, counter):
    url = inst[:-5] + "_1" + ".html"
    print(url)
    web_source = requests.get(url, headers=REQUEST_HEADER)
    if web_source.status_code == 200:
        with open("./" + str(counter) + ".html", "w", encoding="utf-8") as file:
            file.write(web_source.text)
            soup = BeautifulSoup(web_source.content.decode("utf-8"), "lxml")
            # print(soup)
            # sumPage = soup.select(".sumpage")
            # print(sumPage)

            threadBody = soup.select("#zwconbody")


if __name__ == "__main__":
    csvWriter = FileWriter("thread_content_guba_")
    with open(BASE_URLSOURCE, "r") as urlFile:
        counter = 0
        for lines in urlFile.readlines():
            counter += 1
            fetchThread(lines.strip("\n"), counter)
