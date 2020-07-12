import logging
import os
import random
import re
import time
import urllib
import urllib.request
from urllib.parse import urljoin

import m3u8
import requests
from glob import iglob

from natsort import natsorted
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
# pip3 install pycryptodome
from Crypto.Cipher import AES

uapools = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36 Edg/80.0.361.50",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.5",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:48.0) Gecko/20100101 Firefox/48.0",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; .NET4.0E) QQBrowser/6.9.11079.201",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0)"
]


class FindM3U8URL(object):

    def __init__(self):
        self.index_url: str
        self.resultOfCurPageUrl = []
        self.resultOfCurPageName = []
        self.resultName = []

    def log(self):
        if not os.path.exists(".\\log"):
            os.mkdir(".\\log")
        timenow = time.strftime("%Y_%m_%d_%H_%M_%S")
        logfilename = ".\\log\\" + timenow + ".log"
        logging.basicConfig(filename=logfilename, format='%(levelname)s:%(asctime)s:%(message)s', level=logging.INFO,
                            datefmt='[%d/%b/%Y %H:%M:%S]')

    def searchByUrl(self):
        if ("html" in self.index_url):
            pass
        else:
            self.index_url = self.index_url + ".html"
        patOfUrl = '/vodplay/(.*?)-1.html'
        self.urlOut = re.compile(patOfUrl, re.S).findall(self.index_url)[0]
        logging.info("urlOut:" + self.urlOut)

    def randomUA(self):
        opener = urllib.request.build_opener()
        this_ua = random.choice(uapools)
        ua = ("User-Agent", this_ua)
        self.uaForN = "User-Agent:" + this_ua
        opener.addheaders = [ua]
        urllib.request.install_opener(opener)
        logging.info("ua:" + str(this_ua))

    def searchAllUrl(self):
        self.randomUA()
        dataOfFirstPage = urllib.request.urlopen(self.index_url, timeout=60).read().decode("utf-8", "ignore")
        patOfEveryPage = '<a href="/vodplay/' + self.urlOut + '(.*?)">.*?</a></li>'
        patOfName = '<a href="/vodplay/' + self.urlOut + '.*?>(.*?)</a></li>'

        self.resultOfPage = re.compile(patOfEveryPage, re.S).findall(dataOfFirstPage)
        self.resultOfName = re.compile(patOfName, re.S).findall(dataOfFirstPage)

    def findName(self):
        self.randomUA()
        dataOfFirstPage = urllib.request.urlopen(self.index_url, timeout=60).read().decode("utf-8", "ignore")
        pat = "vod_name='(.*?)',"
        self.resultName = re.compile(pat, re.S).findall(dataOfFirstPage)[0]

    def findM3U8(self):
        patOfM3U8 = 'url":"https?:(.*?)","url_next'
        self.randomUA()
        for i in range(self.startindex - 1, self.endindex):
            curPageUrl = "http://lab.liumingye.cn/vodplay/" + self.urlOut + self.resultOfPage[i]
            dataOfCurPage = urllib.request.urlopen(curPageUrl).read().decode("utf-8", "ignore")
            resultOfCurPage = re.compile(patOfM3U8, re.S).findall(dataOfCurPage)[0]
            self.resultOfCurPageUrl.append("http:" + resultOfCurPage.replace('\/', '/'))
            self.resultOfCurPageName.append(self.resultOfName[i])

    def downloadM3U8(self):
        print("共有" + str(len(self.resultOfPage)) + "集/期")
        logging.info("共有" + str(len(self.resultOfPage)) + "集/期")
        self.startindex = int(input("请输入从第几集开始下载:"))
        logging.info(f'从第 {self.startindex} 集/期开始下载')
        self.endindex = int(input("请输入下载到第几集:"))
        logging.info(f'下载到第 {self.endindex} 集/期')

    def run(self):
        self.log()
        self.searchByUrl()
        self.searchAllUrl()
        self.downloadM3U8()
        self.findName()
        self.findM3U8()
        return self.resultName, self.resultOfCurPageUrl, self.resultOfCurPageName


@dataclass
class DownLoadM3U8(object):
    m3u8_url: str
    file_name: str

    def __post_init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
        if not self.file_name:
            self.file_name = time.strftime("%Y_%m_%d_%H_%M_%S") + '_index.mp4'
        self.m3u8_obj = m3u8.load(self.m3u8_url)
        self.cryptor = self.get_key()

    def randomUA(self):
        self.UserAgent = random.choice(uapools)

    def get_key(self):
        """
        获取key进行解密，这里可以获取method加密方式进行解密
        """
        if self.m3u8_obj.keys and self.m3u8_obj.keys[0]:
            res = requests.get(self.m3u8_obj.keys[0].absolute_uri, headers={'User-Agent': self.UserAgent})
            # AES 解密
            return AES.new(res.content, AES.MODE_CBC, res.content)
        else:
            return None

    def get_ts_url(self):
        for seg in self.m3u8_obj.segments:
            yield urljoin(self.m3u8_obj.base_uri, seg.uri)

    def download_ts(self, url_info):
        """
        下载ts文件，写入时如果有加密需要解密
        """
        url, ts_name = url_info
        print(f'download {ts_name} from {url} ')
        logging.info(f'download {ts_name} from {url} ')
        res = requests.get(url, headers={'User-Agent': self.UserAgent})
        with open(ts_name, 'wb') as fp:
            if self.cryptor is not None:
                fp.write(self.cryptor.decrypt(res.content))
            else:
                fp.write(res.content)

    def download_all_ts(self):
        ts_urls = self.get_ts_url()
        for index, ts_url in enumerate(ts_urls):
            self.thread_pool.submit(self.download_ts, [ts_url, f'{index}.ts'])
        self.thread_pool.shutdown()

    def run(self):
        self.randomUA()
        # 如果是第一层M3U8文件，那么就获取第二层的url
        if self.m3u8_obj.playlists and self.m3u8_obj.data.get("playlists"):
            self.m3u8_url = urljoin(self.m3u8_obj.base_uri, self.m3u8_obj.data.get("playlists")[0]["uri"])
            self.__post_init__()
        if not self.m3u8_obj.segments or not self.m3u8_obj.files:
            raise ValueError("m3u8数据不正确，请检查")
        self.download_all_ts()
        print("Download ts files completed")
        logging.info("Download ts files completed")
        ts_path = '*.ts'
        with open(self.file_name, 'wb') as fn:
            for ts in natsorted(iglob(ts_path)):
                with open(ts, 'rb') as ft:
                    sc_line = ft.read()
                    fn.write(sc_line)
            for ts in iglob(ts_path):
                os.remove(ts)
        if os.path.exists("key.key"):
            os.remove("key.key")
        print(f'合并 {self.file_name} 完成')
        logging.info(f'合并 {self.file_name} 完成')


if __name__ == '__main__':
    m3u8_url: str = input("Please input index url:")
    m3u8url = FindM3U8URL()
    m3u8url.index_url = m3u8_url
    prename, urllist, namelist = m3u8url.run()
    # print(namelist)
    for i in range(0, len(urllist)):
        start = time.time()
        save_name = prename + namelist[i] + '.mp4'
        print("正在从" + urllist[i] + "下载" + save_name)
        logging.info("正在从" + urllist[i] + "下载" + save_name)
        print("请耐心等待!")
        print("目录下会生成很多.ts文件,不用担心,下载完成后会自动删除")
        print("正在下载,请稍后!")
        M3U8 = DownLoadM3U8(urllist[i], save_name)
        M3U8.run()
        end = time.time()
        print(f'下载 {save_name} 共耗时 {end - start} 秒')
        logging.info(f'下载 {save_name} 共耗时 {end - start} 秒')
    print("感谢使用,再见!")
    logging.info("感谢使用,再见!")
